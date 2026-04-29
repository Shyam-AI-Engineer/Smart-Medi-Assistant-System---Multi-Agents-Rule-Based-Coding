"""Vital signs API endpoints.

Routes:
  POST /api/v1/vitals/          – store vitals + AI analysis + trend
  GET  /api/v1/vitals/{patient_id} – vitals history (latest first)
  POST /api/v1/vitals/analyze   – stateless analysis only (no storage)
  WS   /api/v1/vitals/ws/{patient_id} – real-time vitals streaming
"""
import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session


from app.schemas.patient_schema import (
    VitalsAnalyzeRequest,
    VitalsAnalyzeResponse,
    VitalAnalysisItem,
)
from app.schemas.vitals_schema import (
    VitalsStoreRequest,
    VitalsStoreResponse,
    VitalRecordResponse,
    VitalsHistoryResponse,
    VitalsHistoryItem,
)
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from app.extensions import get_db
from app.agents.monitoring_agent import get_monitoring_agent
from app.services.vitals_service import VitalsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.post(
    "/analyze",
    response_model=VitalsAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze vital signs",
    description="Analyze vital signs and detect anomalies with automatic escalation"
)
@limiter.limit("20/minute")
def analyze_vitals(
    request: Request,
    vitals_request: VitalsAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
) -> VitalsAnalyzeResponse:
    """
    Analyze vital signs and detect health anomalies.

    The system will:
    1. Compare vitals against medical thresholds
    2. Classify severity (NORMAL → CRITICAL)
    3. Generate LLM-based explanations
    4. Recommend appropriate actions
    5. Escalate to triage if critical

    Args:
        request: VitalsAnalyzeRequest with vital measurements
        current_user: JWT user info (dependency)
        db: Database session (dependency)

    Returns:
        VitalsAnalyzeResponse with analysis, recommendations, and escalation flag

    Raises:
        400: No vitals provided or invalid values
        401: Not authenticated
        500: Internal server error
    """
    try:
        # Build vitals dict from request (only include non-None fields)
        vitals: Dict[str, float] = {}
        if vitals_request.heart_rate is not None:
            vitals["heart_rate"] = vitals_request.heart_rate
        if vitals_request.blood_pressure_systolic is not None:
            vitals["blood_pressure_systolic"] = vitals_request.blood_pressure_systolic
        if vitals_request.blood_pressure_diastolic is not None:
            vitals["blood_pressure_diastolic"] = vitals_request.blood_pressure_diastolic
        if vitals_request.oxygen_saturation is not None:
            vitals["oxygen_saturation"] = vitals_request.oxygen_saturation
        if vitals_request.temperature is not None:
            vitals["temperature"] = vitals_request.temperature
        if vitals_request.respiratory_rate is not None:
            vitals["respiratory_rate"] = vitals_request.respiratory_rate

        # Validate that at least one vital was provided
        if not vitals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one vital sign measurement is required"
            )

        # Build patient info dict if provided
        patient_info: Optional[Dict[str, Any]] = None
        if vitals_request.patient_info:
            patient_info = {
                "age": vitals_request.patient_info.age,
                "medical_history": vitals_request.patient_info.medical_history,
                "current_medications": vitals_request.patient_info.current_medications,
            }

        # Call monitoring agent
        logger.info(
            f"Analyzing vitals for user {current_user['user_id']}: {list(vitals.keys())}"
        )

        agent = get_monitoring_agent()
        agent_response = agent.analyze_vitals(vitals=vitals, patient_info=patient_info)

        # Log result
        logger.info(
            f"Vitals analysis complete: status={agent_response['overall_status']}, "
            f"escalate={agent_response['should_escalate_to_triage']}"
        )

        # Build response from agent dict
        # Convert vital_analyses list to VitalAnalysisItem objects
        vital_analyses = [
            VitalAnalysisItem(
                vital_type=v["vital_type"],
                value=v["value"],
                unit=v["unit"],
                status=v["status"],
                severity=v["severity"],
                normal_range=v["normal_range"],
                explanation=v["explanation"],
                recommendation=v["recommendation"],
                confidence=v["confidence"],
            )
            for v in agent_response.get("vital_analyses", [])
        ]

        return VitalsAnalyzeResponse(
            overall_status=agent_response["overall_status"],
            severity_level=agent_response["severity_level"],
            vital_analyses=vital_analyses,
            critical_findings=agent_response.get("critical_findings", []),
            overall_assessment=agent_response["overall_assessment"],
            recommendations=agent_response.get("recommendations", []),
            should_escalate_to_triage=agent_response["should_escalate_to_triage"],
            confidence_score=agent_response["confidence_score"],
            agent_used=agent_response.get("agent_used", "monitoring"),
            tokens_used=agent_response.get("tokens_used", 0),
            timestamp=agent_response["timestamp"],
            disclaimer=agent_response["disclaimer"],
            response=agent_response["response"],
            error=False,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except ValueError as e:
        logger.warning(f"Validation error in vitals analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error in vitals analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze vital signs. Please try again later."
        )


@router.post(
    "/",
    response_model=VitalsStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store vitals and analyze",
    description="Persist a vitals reading, run AI analysis, and return trend vs recent history",
)
@limiter.limit("30/minute")
def store_vitals(
    request: Request,
    vitals_request: VitalsStoreRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VitalsStoreResponse:
    """
    Store a new vitals record and return immediate AI analysis plus trend.

    - Validates the authenticated user may access the given patient_id.
    - Persists the measurement to the database.
    - Runs MonitoringAgent classification (NORMAL → CRITICAL).
    - Compares against up to 5 recent records to determine trend
      (WORSENING / IMPROVING / STABLE).
    - Marks anomaly_detected=True when status is HIGH or CRITICAL.

    Raises:
        400: No vital measurements provided
        403: Patient may only access own records
        404: Patient not found
        500: Internal server error
    """
    try:
        # ALWAYS derive patient_id from JWT (never trust client input)
        from app.models import Patient
        patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )
        vitals_request.patient_id = patient.id

        service = VitalsService(db)
        result = service.store_and_analyze(vitals_request, current_user)

        return VitalsStoreResponse(
            record=VitalRecordResponse.model_validate(result["record"]),
            analysis=result["analysis"],
            trend=result["trend"],
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error storing vitals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store vital signs. Please try again later.",
        )


@router.get(
    "/{patient_id}",
    response_model=VitalsHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vitals history",
    description="Return paginated vitals history for a patient (newest first)",
)
def get_vitals_history(
    patient_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VitalsHistoryResponse:
    """
    Retrieve paginated vitals history for the specified patient (newest first).

    Access control:
    - Patients may only query their own patient_id.
    - Doctors and admins may query any patient_id.

    Raises:
        403: Patient attempting to access another patient's data
        404: Patient not found
    """
    try:
        service = VitalsService(db)
        result = service.get_history(patient_id, current_user, limit, offset)

        return VitalsHistoryResponse(
            patient_id=result["patient_id"],
            items=[VitalsHistoryItem.model_validate(v) for v in result["items"]],
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"],
            has_next=result["has_next"],
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Unexpected error fetching vitals history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve vitals history. Please try again later.",
        )


@router.websocket("/ws/{patient_id}")
async def websocket_vitals(
    websocket: WebSocket,
    patient_id: str,
):
    """
    WebSocket endpoint for real-time vitals streaming and analysis.

    Client connects and can send vitals in JSON format:
    {
        "heart_rate": 85,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "temperature": 37.2,
        "oxygen_saturation": 98,
        "respiratory_rate": 16
    }

    Server responds with analysis:
    {
        "status": "success",
        "analysis": {...},
        "timestamp": "2026-04-29T10:30:00"
    }

    Or on error:
    {
        "status": "error",
        "message": "Error message"
    }
    """
    try:
        # Accept the connection
        await websocket.accept()
        logger.info(f"WebSocket connected for patient {patient_id}")

        # Simple counter for demo purposes
        message_count = 0

        while True:
            # Receive vitals from client
            data = await websocket.receive_text()
            message_count += 1

            try:
                vitals_data = json.loads(data)

                # Build vitals dict (only include non-None fields)
                vitals: Dict[str, float] = {}
                if vitals_data.get("heart_rate") is not None:
                    vitals["heart_rate"] = float(vitals_data["heart_rate"])
                if vitals_data.get("blood_pressure_systolic") is not None:
                    vitals["blood_pressure_systolic"] = float(vitals_data["blood_pressure_systolic"])
                if vitals_data.get("blood_pressure_diastolic") is not None:
                    vitals["blood_pressure_diastolic"] = float(vitals_data["blood_pressure_diastolic"])
                if vitals_data.get("temperature") is not None:
                    vitals["temperature"] = float(vitals_data["temperature"])
                if vitals_data.get("oxygen_saturation") is not None:
                    vitals["oxygen_saturation"] = float(vitals_data["oxygen_saturation"])
                if vitals_data.get("respiratory_rate") is not None:
                    vitals["respiratory_rate"] = float(vitals_data["respiratory_rate"])

                if not vitals:
                    await websocket.send_json({
                        "status": "error",
                        "message": "No vital measurements provided"
                    })
                    continue

                # Analyze vitals
                logger.info(f"WebSocket vitals received (msg #{message_count}): {list(vitals.keys())}")
                agent = get_monitoring_agent()
                analysis = agent.analyze_vitals(vitals=vitals, patient_info=None)

                # Send analysis result back to client
                await websocket.send_json({
                    "status": "success",
                    "vitals": vitals,
                    "analysis": analysis,
                    "timestamp": analysis.get("timestamp"),
                })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid JSON format"
                })
            except ValueError as e:
                await websocket.send_json({
                    "status": "error",
                    "message": f"Invalid vital value: {str(e)}"
                })
            except Exception as e:
                logger.error(f"WebSocket analysis error: {e}")
                await websocket.send_json({
                    "status": "error",
                    "message": "Failed to analyze vitals"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for patient {patient_id}")
    except Exception as e:
        logger.error(f"WebSocket error for patient {patient_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass
