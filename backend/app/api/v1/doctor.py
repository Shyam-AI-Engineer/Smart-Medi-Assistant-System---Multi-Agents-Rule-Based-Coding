"""Doctor dashboard API endpoints.

Routes:
  GET /api/v1/doctor/patients           – list all patients (paginated)
  GET /api/v1/doctor/patients/{id}      – patient detail + vitals + chat history
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import require_role
from app.extensions import get_db
from app.models import Patient, User, Vitals, ChatHistory
from app.schemas.patient_schema import PatientProfileResponse, VitalsResponse
from app.schemas.chat_schema import ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doctor", tags=["doctor"])


class PatientSummaryResponse(PatientProfileResponse):
    """Patient summary for list view."""
    full_name: str = ""
    latest_vital_status: str = "UNKNOWN"  # NORMAL, MODERATE, HIGH, CRITICAL
    risk_level: str = "UNKNOWN"  # LOW, MODERATE, HIGH, CRITICAL
    latest_vital_timestamp: Optional[str] = None
    latest_vital_id: Optional[str] = None


class PatientDetailResponse(PatientProfileResponse):
    """Detailed patient view with vitals and chat history."""
    user: Dict[str, Any]  # user_id, email, full_name
    vitals: List[VitalsResponse] = []
    chat_history: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}  # latest_status, risk_level, total_messages


@router.get(
    "/patients",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List all patients",
    description="Retrieve paginated list of all patients (doctor view)",
)
def list_all_patients(
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieve paginated list of all patients accessible to doctor.

    Args:
        limit: Max records per page (1-100, default 20)
        offset: Skip N records for pagination (default 0)
        current_user: Doctor user (JWT validated, role="doctor")
        db: Database session

    Returns:
        {
            "items": [
                {
                    "id": "...",
                    "full_name": "John Doe",
                    "age": 45,
                    "latest_vital_status": "NORMAL" | "MODERATE" | "HIGH" | "CRITICAL",
                    "risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
                    "latest_vital_timestamp": "2026-04-27T10:30:00"
                }
            ],
            "total": 42,
            "limit": 20,
            "offset": 0,
            "has_next": True
        }
    """
    try:
        # Get total count
        total = db.query(Patient).count()

        # Get paginated patients
        patients = (
            db.query(Patient)
            .join(User)
            .order_by(Patient.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Build response items with latest vital info
        items = []
        for patient in patients:
            # Get latest vital
            latest_vital = (
                db.query(Vitals)
                .filter(Vitals.patient_id == patient.id)
                .order_by(Vitals.created_at.desc())
                .first()
            )

            # Calculate age if date_of_birth exists
            from datetime import datetime
            age = None
            if patient.date_of_birth:
                today = datetime.utcnow().date()
                age = (
                    today.year
                    - patient.date_of_birth.year
                    - (
                        (today.month, today.day)
                        < (patient.date_of_birth.month, patient.date_of_birth.day)
                    )
                )

            # Determine status from latest vital
            status_val = "UNKNOWN"
            risk_level = "UNKNOWN"
            if latest_vital:
                # Simple heuristic: check if any anomaly detected
                if latest_vital.anomaly_detected:
                    if latest_vital.anomaly_score and latest_vital.anomaly_score > 0.8:
                        status_val = "CRITICAL"
                        risk_level = "CRITICAL"
                    elif latest_vital.anomaly_score and latest_vital.anomaly_score > 0.6:
                        status_val = "HIGH"
                        risk_level = "HIGH"
                    else:
                        status_val = "MODERATE"
                        risk_level = "MODERATE"
                else:
                    status_val = "NORMAL"
                    risk_level = "LOW"

            items.append(
                {
                    "id": patient.id,
                    "user_id": patient.user_id,
                    "full_name": patient.user.full_name if patient.user else "Unknown",
                    "age": age,
                    "date_of_birth": patient.date_of_birth.isoformat()
                    if patient.date_of_birth
                    else None,
                    "latest_vital_status": status_val,
                    "risk_level": risk_level,
                    "latest_vital_timestamp": latest_vital.created_at.isoformat()
                    if latest_vital
                    else None,
                    "latest_vital_id": latest_vital.id if latest_vital else None,
                }
            )

        has_next = (offset + limit) < total

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": has_next,
        }

    except Exception as e:
        logger.error(f"Error listing patients: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient list",
        )


@router.get(
    "/patients/{patient_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get patient details",
    description="Retrieve detailed patient view with vitals and chat history",
)
def get_patient_detail(
    patient_id: str,
    vitals_limit: int = Query(
        default=30, ge=1, le=100, description="Max vitals records"
    ),
    chat_limit: int = Query(
        default=20, ge=1, le=100, description="Max chat history records"
    ),
    current_user: dict = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Retrieve detailed patient view including:
    - Patient profile
    - Paginated vitals history (newest first)
    - Paginated chat history (newest first)
    - Summary (latest status, risk level, message count)

    Args:
        patient_id: Patient UUID
        vitals_limit: Max vitals to return (1-100)
        chat_limit: Max chat messages to return (1-100)
        current_user: Doctor user (JWT validated)
        db: Database session

    Returns:
        {
            "patient": {...},
            "vitals": [...],
            "chat_history": [...],
            "summary": {
                "latest_status": "NORMAL" | "HIGH" | "CRITICAL",
                "risk_level": "LOW" | "HIGH" | "CRITICAL",
                "total_messages": 42,
                "latest_vital_at": "2026-04-27T10:30:00"
            }
        }
    """
    try:
        # Get patient
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
            )

        # Get vitals (paginated, newest first)
        vitals = (
            db.query(Vitals)
            .filter(Vitals.patient_id == patient_id)
            .order_by(Vitals.created_at.desc())
            .limit(vitals_limit)
            .all()
        )

        # Get chat history (paginated, newest first)
        chats = (
            db.query(ChatHistory)
            .filter(ChatHistory.patient_id == patient_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(chat_limit)
            .all()
        )

        # Build patient dict with user info
        patient_dict = PatientProfileResponse.model_validate(patient).model_dump()
        patient_dict["user"] = {
            "user_id": patient.user.id,
            "email": patient.user.email,
            "full_name": patient.user.full_name,
        }

        # Build vitals list
        vitals_list = [VitalsResponse.model_validate(v).model_dump() for v in vitals]

        # Build chat history list
        chat_list = [
            {
                "id": c.id,
                "user_message": c.user_message,
                "ai_response": c.ai_response,
                "agent_used": c.agent_used,
                "confidence_score": c.confidence_score,
                "created_at": c.created_at.isoformat(),
            }
            for c in chats
        ]

        # Calculate summary
        latest_vital = vitals[0] if vitals else None
        latest_status = "UNKNOWN"
        risk_level = "UNKNOWN"

        if latest_vital:
            if latest_vital.anomaly_detected:
                if latest_vital.anomaly_score and latest_vital.anomaly_score > 0.8:
                    latest_status = "CRITICAL"
                    risk_level = "CRITICAL"
                elif latest_vital.anomaly_score and latest_vital.anomaly_score > 0.6:
                    latest_status = "HIGH"
                    risk_level = "HIGH"
                else:
                    latest_status = "MODERATE"
                    risk_level = "MODERATE"
            else:
                latest_status = "NORMAL"
                risk_level = "LOW"

        # Total message count (not paginated, for reference)
        total_messages = db.query(ChatHistory).filter(
            ChatHistory.patient_id == patient_id
        ).count()

        summary = {
            "latest_status": latest_status,
            "risk_level": risk_level,
            "total_messages": total_messages,
            "latest_vital_at": latest_vital.created_at.isoformat()
            if latest_vital
            else None,
        }

        return {
            "patient": patient_dict,
            "vitals": vitals_list,
            "chat_history": chat_list,
            "summary": summary,
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting patient detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient details",
        )
