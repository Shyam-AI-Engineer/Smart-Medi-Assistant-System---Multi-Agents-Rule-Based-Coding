"""Vitals CRUD endpoints - store and retrieve vital signs."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

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
from app.services.vitals_service import VitalsService
from app.utils.audit import write_audit, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.post(
    "/",
    response_model=VitalsStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store vitals and analyze",
)
@limiter.limit("30/minute")
def store_vitals(
    request: Request,
    vitals_request: VitalsStoreRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VitalsStoreResponse:
    """Persist a vitals record, run AI analysis, and return trend vs recent history."""
    from app.models import Patient
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    vitals_request.patient_id = patient.id

    result = VitalsService(db).store_and_analyze(vitals_request, current_user)
    response = VitalsStoreResponse(
        record=VitalRecordResponse.model_validate(result["record"]),
        analysis=result["analysis"],
        trend=result["trend"],
    )
    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="record_vitals",
        resource_type="vitals",
        resource_id=response.record.id,
        ip_address=get_client_ip(request),
        details=f"status={result['analysis'].get('overall_status', 'unknown')} trend={result['trend']}",
    )
    return response


@router.get(
    "/{patient_id}",
    response_model=VitalsHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vitals history",
)
def get_vitals_history(
    request: Request,
    patient_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VitalsHistoryResponse:
    """Paginated vitals history for a patient (newest first)."""
    result = VitalsService(db).get_history(patient_id, current_user, limit, offset)

    # Audit logging: PHI access (viewing vitals history)
    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="view_vitals",
        resource_type="vitals",
        resource_id=patient_id,
        ip_address=get_client_ip(request),
        details=f"limit={limit} offset={offset} total={result['total']}",
    )

    return VitalsHistoryResponse(
        patient_id=result["patient_id"],
        items=[VitalsHistoryItem.model_validate(v) for v in result["items"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        has_next=result["has_next"],
    )
