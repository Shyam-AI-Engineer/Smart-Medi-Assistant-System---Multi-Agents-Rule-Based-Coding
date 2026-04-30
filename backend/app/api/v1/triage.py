"""Triage API endpoint — symptom urgency assessment.

Routes:
  POST /api/v1/triage/assess  – assess symptom urgency
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.models import Patient
from app.agents.triage_agent import get_triage_agent
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from app.extensions import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triage", tags=["triage"])


class TriageRequest(BaseModel):
    symptoms: str = Field(..., min_length=5, max_length=2000, description="Patient symptom description")


class TriageResponse(BaseModel):
    urgency_level: str
    severity_score: int
    requires_escalation: bool
    escalation_path: str
    immediate_action: str
    reasoning: str
    warning_signs: List[str]
    next_steps: List[str]
    confidence_score: float
    agent_used: str
    response: str
    disclaimer: str
    error: Optional[str] = None


@router.post(
    "/assess",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
def assess_symptoms(
    request: Request,
    payload: TriageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TriageResponse:
    """
    Assess symptom urgency using the Triage Agent.

    Returns urgency level, severity score, escalation path, and immediate
    action recommendations.
    """
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()

    patient_info = None
    if patient:
        from datetime import date

        def _age(dob) -> Optional[int]:
            if not dob:
                return None
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        patient_info = {
            "age": _age(patient.date_of_birth),
            "allergies": patient.allergies,
            "current_medications": patient.current_medications,
            "medical_history": patient.medical_history,
        }

    agent = get_triage_agent()
    result = agent.assess_urgency(
        patient_message=payload.symptoms,
        patient_info=patient_info,
    )

    logger.info(
        "triage.assessed",
        extra={
            "user_id": current_user["user_id"],
            "urgency_level": result.get("urgency_level"),
            "severity_score": result.get("severity_score"),
        },
    )

    return TriageResponse(
        urgency_level=result.get("urgency_level", "moderate"),
        severity_score=result.get("severity_score", 5),
        requires_escalation=result.get("requires_escalation", False),
        escalation_path=result.get("escalation_path", "Doctor Visit"),
        immediate_action=result.get("immediate_action", ""),
        reasoning=result.get("reasoning", ""),
        warning_signs=result.get("warning_signs", []),
        next_steps=result.get("next_steps", []),
        confidence_score=result.get("confidence_score", 0.9),
        agent_used=result.get("agent_used", "triage"),
        response=result.get("response", ""),
        disclaimer=result.get("disclaimer", ""),
        error=result.get("error"),
    )
