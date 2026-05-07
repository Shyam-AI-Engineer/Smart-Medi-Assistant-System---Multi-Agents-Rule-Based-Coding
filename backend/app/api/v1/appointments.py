"""Appointment endpoints.

Routes (patient):
  GET    /appointments/         – list own appointments
  POST   /appointments/         – request an appointment
  DELETE /appointments/{id}     – cancel a pending appointment
  GET    /appointments/files/{id}/{filename} – download attachment

Routes (doctor via /doctor prefix, added in doctor.py):
  GET    /doctor/appointments   – all pending appointments for doctor's patients
  PUT    /doctor/appointments/{id} – update status/schedule
"""
import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.models import Patient, User
from app.models.appointment import Appointment
from app.middleware.auth_middleware import get_current_user
from app.extensions import get_db
from app.schemas.appointment_schema import AppointmentItem, AppointmentListResponse
from app.schemas.message_schema import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["appointments"])

_ALLOWED_ATTACH_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".docx"}
_MAX_ATTACH_BYTES = 10 * 1024 * 1024

# Construct absolute path for file storage
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend/
_ATTACH_DIR = os.path.join(_BACKEND_DIR, "..", "data", "appointment_attachments")
_ATTACH_DIR = os.path.abspath(_ATTACH_DIR)  # Resolve to absolute path

logger.info(f"Attachment directory configured: {_ATTACH_DIR}")


def _appt_dict(a: Appointment, doctor_name: str | None) -> dict:
    return {
        "id": a.id,
        "patient_id": a.patient_id,
        "doctor_user_id": a.doctor_user_id,
        "doctor_name": doctor_name,
        "reason": a.reason,
        "preferred_date": a.preferred_date,
        "preferred_time_slot": a.preferred_time_slot,
        "status": a.status,
        "doctor_notes": a.doctor_notes,
        "scheduled_at": a.scheduled_at,
        "ai_suggested": a.ai_suggested,
        "attachment_path": a.attachment_path,
        "created_at": a.created_at.isoformat(),
    }


@router.get("/", response_model=AppointmentListResponse, summary="List patient's own appointments")
def list_appointments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentListResponse:
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    appts = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient.id)
        .order_by(Appointment.created_at.desc())
        .all()
    )

    doctor_ids = {a.doctor_user_id for a in appts if a.doctor_user_id}
    doctors = {
        u.id: u.full_name
        for u in db.query(User).filter(User.id.in_(doctor_ids)).all()
    } if doctor_ids else {}

    items = [_appt_dict(a, doctors.get(a.doctor_user_id)) for a in appts]
    return {"items": items, "total": len(items)}


@router.post(
    "/",
    response_model=AppointmentItem,
    status_code=status.HTTP_201_CREATED,
    summary="Request a new appointment",
)
async def request_appointment(
    reason: str = Form(...),
    preferred_date: str | None = Form(None),
    preferred_time_slot: str | None = Form(None),
    ai_suggested: bool = Form(False),
    attachment: UploadFile | None = File(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AppointmentItem:
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    appt = Appointment(
        patient_id=patient.id,
        reason=reason,
        preferred_date=preferred_date,
        preferred_time_slot=preferred_time_slot,
        ai_suggested=ai_suggested,
        status="pending",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    if attachment and attachment.filename:
        logger.info(f"Processing attachment: {attachment.filename}")
        fname_lower = attachment.filename.lower()
        ext = os.path.splitext(fname_lower)[1]
        if ext not in _ALLOWED_ATTACH_EXT:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(sorted(_ALLOWED_ATTACH_EXT))}",
            )

        content = await attachment.read()
        logger.info(f"Attachment read: {len(content)} bytes")
        if len(content) > _MAX_ATTACH_BYTES:
            raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

        try:
            logger.info(f"Creating directory: {_ATTACH_DIR}")
            os.makedirs(_ATTACH_DIR, exist_ok=True)
            saved_fname = f"{appt.id}_{attachment.filename}"
            saved_path = os.path.join(_ATTACH_DIR, saved_fname)

            logger.info(f"Saving file to: {saved_path}")
            with open(saved_path, "wb") as f:
                bytes_written = f.write(content)

            logger.info(f"File written: {bytes_written} bytes to {saved_path}")

            # Verify file exists
            if os.path.exists(saved_path):
                logger.info(f"File verified to exist: {saved_path}")
            else:
                logger.error(f"File was not created: {saved_path}")
                raise HTTPException(status_code=500, detail="File save verification failed")

            appt.attachment_path = saved_fname
            db.commit()
            db.refresh(appt)
            logger.info(f"Database updated with attachment_path: {saved_fname}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to save attachment: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to save attachment: {str(e)}")

    return _appt_dict(appt, None)


@router.delete("/{appointment_id}", response_model=SuccessResponse, summary="Cancel a pending appointment")
def cancel_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    appt = db.query(Appointment).filter_by(id=appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appt.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if appt.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Only pending appointments can be cancelled")

    appt.status = "cancelled"
    db.commit()
    return {"success": True}


@router.get("/files/{appointment_id}/{filename}", summary="Download appointment attachment")
def download_attachment(
    appointment_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Download request: appt_id={appointment_id}, filename={filename}, user_role={current_user.get('role')}")

    appt = db.query(Appointment).filter_by(id=appointment_id).first()
    if not appt:
        logger.warning(f"Appointment not found: {appointment_id}")
        raise HTTPException(status_code=404, detail="Appointment not found")

    logger.info(f"Appointment found: {appt.id}, attachment_path={appt.attachment_path}")

    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    is_patient = patient and appt.patient_id == patient.id
    is_doctor = current_user.get("role") in ("doctor", "admin")

    logger.info(f"Access check: is_patient={is_patient}, is_doctor={is_doctor}")
    if not (is_patient or is_doctor):
        logger.warning(f"Access denied for user {current_user.get('user_id')}")
        raise HTTPException(status_code=403, detail="Forbidden")

    if not appt.attachment_path or appt.attachment_path != filename:
        logger.warning(f"Attachment mismatch: stored={appt.attachment_path}, requested={filename}")
        raise HTTPException(status_code=404, detail="Attachment not found")

    file_path = os.path.join(_ATTACH_DIR, filename)
    logger.info(f"Checking file at: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        logger.info(f"Attachment directory contents: {os.listdir(_ATTACH_DIR) if os.path.exists(_ATTACH_DIR) else 'DIR NOT FOUND'}")
        raise HTTPException(status_code=404, detail="File not found on disk")

    logger.info(f"File found, sending: {file_path}")
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename.split("_", 1)[1] if "_" in filename else filename,
    )
