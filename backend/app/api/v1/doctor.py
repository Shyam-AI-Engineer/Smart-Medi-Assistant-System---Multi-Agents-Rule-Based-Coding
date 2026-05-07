"""Doctor dashboard API endpoints."""
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import require_role
from app.extensions import get_db
from app.schemas.message_schema import SendMessageRequest
from app.schemas.appointment_schema import AppointmentUpdateRequest
from app.services.doctor_service import DoctorService
from app.utils.audit import write_audit, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get(
    "/patients",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="List all patients",
)
def list_all_patients(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return DoctorService(db).list_patients(
        doctor_user_id=current_user["user_id"],
        role=current_user["role"],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/patients/{patient_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get patient details",
)
def get_patient_detail(
    request: Request,
    patient_id: str,
    vitals_limit: int = Query(default=30, ge=1, le=100),
    chat_limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    result = DoctorService(db).get_patient_detail(
        patient_id=patient_id,
        doctor_user_id=current_user["user_id"],
        role=current_user["role"],
        vitals_limit=vitals_limit,
        chat_limit=chat_limit,
    )
    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="view_patient",
        resource_type="patient",
        resource_id=patient_id,
        ip_address=get_client_ip(request),
        details=f"vitals={len(result['vitals'])} chats={len(result['chat_history'])}",
    )
    return result


@router.post(
    "/patients/{patient_id}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to a patient",
)
def send_message_to_patient(
    patient_id: str,
    request_body: SendMessageRequest,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return DoctorService(db).send_message(
        patient_id=patient_id,
        doctor_user_id=current_user["user_id"],
        role=current_user["role"],
        body=request_body.body,
    )


@router.get(
    "/patients/{patient_id}/messages",
    summary="Get message thread with a patient",
)
def get_patient_thread(
    patient_id: str,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return DoctorService(db).get_thread(
        patient_id=patient_id,
        doctor_user_id=current_user["user_id"],
        role=current_user["role"],
    )


@router.get(
    "/messages/unread-count",
    status_code=status.HTTP_200_OK,
    summary="Get unread message count",
)
def get_unread_message_count(
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return DoctorService(db).get_unread_count(doctor_user_id=current_user["user_id"])


@router.get(
    "/patients/{patient_id}/export",
    status_code=status.HTTP_200_OK,
    summary="Export patient summary as PDF",
)
def export_patient_summary_pdf(
    patient_id: str,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from app.utils.pdf_generator import generate_doctor_patient_summary_pdf

    data = DoctorService(db).get_patient_export_data(
        patient_id=patient_id,
        doctor_user_id=current_user["user_id"],
        role=current_user["role"],
    )
    patient = data["patient"]
    dob = patient.date_of_birth.isoformat() if patient.date_of_birth else None
    pdf_buf = generate_doctor_patient_summary_pdf(
        patient_name=data["patient_name"],
        patient_email=data["patient_email"],
        date_of_birth=dob,
        allergies=patient.allergies,
        current_medications=patient.current_medications,
        medical_history=patient.medical_history,
        emergency_contact=patient.emergency_contact,
        vitals=data["vitals_data"],
        summary=data["summary"],
        doctor_name=data["doctor_name"],
    )
    filename = f"patient_summary_{data['patient_name'].replace(' ', '_')}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/appointments", summary="List all patient appointment requests")
def list_doctor_appointments(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return DoctorService(db).list_appointments(
        doctor_user_id=current_user["user_id"],
        role=current_user["role"],
        status_filter=status_filter,
    )


@router.put("/appointments/{appointment_id}", summary="Update appointment status / schedule")
def update_appointment(
    appointment_id: str,
    body: AppointmentUpdateRequest,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    return DoctorService(db).update_appointment(
        appointment_id=appointment_id,
        doctor_user_id=current_user["user_id"],
        role=current_user["role"],
        update=body,
    )
