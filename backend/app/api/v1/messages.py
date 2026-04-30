"""Patient-side messaging endpoints.

Routes:
  GET    /messages/             – patient inbox (all threads, newest first)
  PATCH  /messages/{id}/read   – mark one message as read
  POST   /messages/reply        – patient replies to a doctor's thread
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models import Patient, User
from app.models.doctor_message import DoctorMessage
from app.schemas.message_schema import ReplyRequest
from app.middleware.auth_middleware import get_current_user
from app.extensions import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


def _msg_dict(m: DoctorMessage, doctor_name: str) -> dict:
    return {
        "id": m.id,
        "patient_id": m.patient_id,
        "doctor_user_id": m.doctor_user_id,
        "doctor_name": doctor_name,
        "body": m.body,
        "sender_role": m.sender_role,
        "is_read": m.is_read,
        "created_at": m.created_at.isoformat(),
    }


@router.get("/", summary="Patient inbox – all messages from doctors")
def get_inbox(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    messages = (
        db.query(DoctorMessage)
        .filter(DoctorMessage.patient_id == patient.id)
        .order_by(DoctorMessage.created_at.desc())
        .all()
    )

    doctor_ids = {m.doctor_user_id for m in messages}
    doctors = {
        u.id: u.full_name
        for u in db.query(User).filter(User.id.in_(doctor_ids)).all()
    }

    items = [_msg_dict(m, doctors.get(m.doctor_user_id, "Doctor")) for m in messages]
    # Unread = doctor-sent messages the patient hasn't seen yet
    unread_count = sum(
        1 for m in messages if m.sender_role == "doctor" and not m.is_read
    )

    return {"items": items, "total": len(items), "unread_count": unread_count}


@router.patch("/{message_id}/read", summary="Mark a doctor message as read")
def mark_read(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    msg = db.query(DoctorMessage).filter_by(id=message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    msg.is_read = True
    db.commit()
    return {"success": True}


@router.post(
    "/reply",
    status_code=status.HTTP_201_CREATED,
    summary="Patient replies to a doctor's thread",
)
def reply_to_doctor(
    body: ReplyRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    doctor = db.query(User).filter_by(id=body.doctor_user_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    msg = DoctorMessage(
        patient_id=patient.id,
        doctor_user_id=body.doctor_user_id,
        body=body.body,
        sender_role="patient",
        is_read=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return _msg_dict(msg, doctor.full_name)
