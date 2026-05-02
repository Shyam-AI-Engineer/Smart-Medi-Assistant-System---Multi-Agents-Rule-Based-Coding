"""Appointment endpoints.

Routes (patient):
  GET    /appointments/         – list own appointments
  POST   /appointments/         – request an appointment
  DELETE /appointments/{id}     – cancel a pending appointment

Routes (doctor via /doctor prefix, added in doctor.py):
  GET    /doctor/appointments   – all pending appointments for doctor's patients
  PUT    /doctor/appointments/{id} – update status/schedule
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import Patient, User
from app.models.appointment import Appointment
from app.schemas.appointment_schema import AppointmentRequest, AppointmentItem, AppointmentListResponse
from app.middleware.auth_middleware import get_current_user
from app.extensions import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["appointments"])


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
        "created_at": a.created_at.isoformat(),
    }


@router.get("/", summary="List patient's own appointments")
def list_appointments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
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
    status_code=status.HTTP_201_CREATED,
    summary="Request a new appointment",
)
def request_appointment(
    body: AppointmentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    appt = Appointment(
        patient_id=patient.id,
        reason=body.reason,
        preferred_date=body.preferred_date,
        preferred_time_slot=body.preferred_time_slot,
        ai_suggested=body.ai_suggested,
        status="pending",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    return _appt_dict(appt, None)


@router.delete("/{appointment_id}", summary="Cancel a pending appointment")
def cancel_appointment(
    appointment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
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
