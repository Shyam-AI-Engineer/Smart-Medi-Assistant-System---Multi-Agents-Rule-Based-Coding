"""Vitals analysis endpoint - stateless AI analysis without storage."""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.schemas.patient_schema import VitalsAnalyzeRequest, VitalsAnalyzeResponse, VitalAnalysisItem
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from app.extensions import get_db
from app.agents.monitoring_agent import get_monitoring_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.post(
    "/analyze",
    response_model=VitalsAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze vital signs",
)
@limiter.limit("20/minute")
def analyze_vitals(
    request: Request,
    vitals_request: VitalsAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
) -> VitalsAnalyzeResponse:
    """Analyze vital signs against medical thresholds and return severity classification."""
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

    if not vitals:
        raise HTTPException(status_code=400, detail="At least one vital sign measurement is required")

    patient_info: Optional[Dict[str, Any]] = None
    if vitals_request.patient_info:
        patient_info = {
            "age": vitals_request.patient_info.age,
            "medical_history": vitals_request.patient_info.medical_history,
            "current_medications": vitals_request.patient_info.current_medications,
        }

    try:
        agent_response = get_monitoring_agent().analyze_vitals(vitals=vitals, patient_info=patient_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Vitals analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to analyze vital signs. Please try again later.")

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
