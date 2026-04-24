"""Patient routes: profile read/update and vitals recording."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.middleware.auth_middleware import get_current_user, require_role
from app.services.patient_service import PatientService
from app.schemas.patient_schema import (
    PatientProfileResponse,
    PatientProfileUpdate,
    VitalsCreate,
    VitalsResponse,
    VitalsListResponse,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get(
    "/me",
    response_model=PatientProfileResponse,
    summary="Get own patient profile",
)
def get_my_profile(
    current_user: dict = Depends(require_role("patient", "doctor", "admin")),
    db: Session = Depends(get_db),
):
    """
    Return the patient profile linked to the current user's account.

    Accessible by patient, doctor, and admin roles.
    """
    patient = PatientService(db).get_by_user_id(current_user["user_id"])
    return PatientProfileResponse.model_validate(patient)


@router.put(
    "/me",
    response_model=PatientProfileResponse,
    summary="Update own patient profile",
)
def update_my_profile(
    update: PatientProfileUpdate,
    current_user: dict = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    """
    Partially update the current patient's profile.

    Only provided fields are changed; omitted fields remain unchanged.
    Only the patient themselves may update their own profile.
    """
    patient = PatientService(db).update(current_user["user_id"], update)
    return PatientProfileResponse.model_validate(patient)


@router.post(
    "/me/vitals",
    response_model=VitalsResponse,
    status_code=201,
    summary="Record vital signs",
)
def record_vitals(
    data: VitalsCreate,
    current_user: dict = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    """
    Submit a new vitals reading. All fields are optional — submit only what
    was measured.

    The Monitoring Agent can later analyze these for anomalies.
    """
    vitals = PatientService(db).add_vitals(current_user["user_id"], data)
    return VitalsResponse.model_validate(vitals)


@router.get(
    "/me/vitals",
    response_model=VitalsListResponse,
    summary="Get vitals history",
)
def get_vitals_history(
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(require_role("patient", "doctor", "admin")),
    db: Session = Depends(get_db),
):
    """
    Return paginated vitals history for the current patient, ordered
    newest-first.
    """
    result = PatientService(db).get_vitals(current_user["user_id"], limit, offset)
    return VitalsListResponse(
        items=[VitalsResponse.model_validate(v) for v in result["items"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        has_next=result["has_next"],
    )
