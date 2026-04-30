"""Medications API endpoints.

Routes:
  GET  /api/v1/medications/          – list patient's active medications
  POST /api/v1/medications/          – add a medication
  DELETE /api/v1/medications/{id}    – remove a medication
  GET  /api/v1/medications/interactions – check interactions for all active meds
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models import Patient
from app.schemas.medication_schema import (
    MedicationRequest,
    MedicationResponse,
    MedicationsListResponse,
    InteractionCheckResponse,
)
from app.services.medication_service import MedicationService
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from app.extensions import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/medications", tags=["medications"])


def _get_patient(db: Session, user_id: str) -> Patient:
    patient = db.query(Patient).filter_by(user_id=user_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient


@router.get("/", response_model=MedicationsListResponse)
def list_medications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicationsListResponse:
    """List active medications for the authenticated patient."""
    patient = _get_patient(db, current_user["user_id"])
    service = MedicationService(db)
    meds = service.list_medications(patient.id)
    return MedicationsListResponse(
        items=[MedicationResponse.model_validate(m) for m in meds],
        total=len(meds),
    )


@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def add_medication(
    request: Request,
    payload: MedicationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MedicationResponse:
    """Add a medication to the patient's active list."""
    patient = _get_patient(db, current_user["user_id"])
    service = MedicationService(db)
    med = service.add_medication(patient.id, payload.model_dump())
    logger.info("medication.added", extra={"patient_id": patient.id, "med": med.medication_name})
    return MedicationResponse.model_validate(med)


@router.delete("/{medication_id}", status_code=status.HTTP_200_OK)
def delete_medication(
    medication_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Remove a medication from the patient's list."""
    patient = _get_patient(db, current_user["user_id"])
    service = MedicationService(db)
    deleted = service.delete_medication(medication_id, patient.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {"success": True}


@router.get("/interactions", response_model=InteractionCheckResponse)
@limiter.limit("10/minute")
def check_interactions(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InteractionCheckResponse:
    """Run AI interaction check across all active medications."""
    patient = _get_patient(db, current_user["user_id"])
    service = MedicationService(db)
    result = service.check_interactions(patient.id)
    return InteractionCheckResponse(**result)
