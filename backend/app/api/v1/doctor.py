"""Doctor dashboard API endpoints.

Routes:
  GET  /api/v1/doctor/patients                      – list all patients (paginated)
  GET  /api/v1/doctor/patients/{id}                 – patient detail + vitals + chat history
  POST /api/v1/doctor/patients/{id}/messages        – send message to patient
  GET  /api/v1/doctor/patients/{id}/messages        – get thread with patient
  GET  /api/v1/doctor/messages/unread-count         – unread message count by patient
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import require_role
from app.extensions import get_db
from app.models import Patient, User, Vitals, ChatHistory
from app.models.doctor_message import DoctorMessage
from app.models.appointment import Appointment
from app.schemas.patient_schema import PatientProfileResponse, VitalsResponse
from app.schemas.chat_schema import ChatResponse
from app.schemas.message_schema import SendMessageRequest
from app.utils.audit import write_audit, get_client_ip

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
    current_user: dict = Depends(require_role("doctor", "admin")),
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
    request: Request,
    patient_id: str,
    vitals_limit: int = Query(
        default=30, ge=1, le=100, description="Max vitals records"
    ),
    chat_limit: int = Query(
        default=20, ge=1, le=100, description="Max chat history records"
    ),
    current_user: dict = Depends(require_role("doctor", "admin")),
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

        write_audit(
            db,
            user_id=current_user["user_id"],
            user_email=current_user["email"],
            user_role=current_user["role"],
            action="view_patient",
            resource_type="patient",
            resource_id=patient_id,
            ip_address=get_client_ip(request),
            details=f"vitals={len(vitals_list)} chats={len(chat_list)}",
        )

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


def _msg_dict(m: DoctorMessage, doctor_name: str) -> Dict[str, Any]:
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
    """Doctor sends a direct message to a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor = db.query(User).filter(User.id == current_user["user_id"]).first()
    doctor_name = doctor.full_name if doctor else "Doctor"

    msg = DoctorMessage(
        patient_id=patient_id,
        doctor_user_id=current_user["user_id"],
        body=request_body.body,
        sender_role="doctor",
        is_read=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    logger.info(f"Doctor {current_user['user_id']} sent message to patient {patient_id}")
    return _msg_dict(msg, doctor_name)


@router.get(
    "/patients/{patient_id}/messages",
    summary="Get message thread with a patient",
)
def get_patient_thread(
    patient_id: str,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve the full message thread between this doctor and a patient.
    Also marks any patient replies as read."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor = db.query(User).filter(User.id == current_user["user_id"]).first()
    doctor_name = doctor.full_name if doctor else "Doctor"

    messages = (
        db.query(DoctorMessage)
        .filter(
            DoctorMessage.patient_id == patient_id,
            DoctorMessage.doctor_user_id == current_user["user_id"],
        )
        .order_by(DoctorMessage.created_at.asc())
        .all()
    )

    # Doctor opening the thread marks patient replies as read
    for m in messages:
        if m.sender_role == "patient" and not m.is_read:
            m.is_read = True
    db.commit()

    items = [_msg_dict(m, doctor_name) for m in messages]
    return {"items": items, "total": len(items), "unread_count": 0}


# ── Unread message count ─────────────────────────────────────────────────────

@router.get(
    "/messages/unread-count",
    status_code=status.HTTP_200_OK,
    summary="Get unread message count",
    description="Get total unread messages and breakdown by patient",
)
def get_unread_message_count(
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get unread message count for doctor from patients.

    Returns:
        {
            "total_unread": 5,
            "by_patient": [
                {
                    "patient_id": "...",
                    "patient_name": "John Doe",
                    "count": 3
                },
                {
                    "patient_id": "...",
                    "patient_name": "Jane Smith",
                    "count": 2
                }
            ]
        }
    """
    from sqlalchemy import func

    # Get unread messages from patients
    unread_query = db.query(
        DoctorMessage.patient_id,
        func.count(DoctorMessage.id).label("count"),
    ).filter(
        DoctorMessage.doctor_user_id == current_user["user_id"],
        DoctorMessage.sender_role == "patient",
        DoctorMessage.is_read == False,  # noqa: E712
    ).group_by(DoctorMessage.patient_id).all()

    total_unread = sum(r.count for r in unread_query)

    # Get patient names for each
    by_patient = []
    for row in unread_query:
        patient = db.query(Patient).filter(Patient.id == row.patient_id).first()
        if patient and patient.user:
            by_patient.append({
                "patient_id": row.patient_id,
                "patient_name": patient.user.full_name,
                "count": row.count,
            })

    return {
        "total_unread": total_unread,
        "by_patient": by_patient,
    }


# ── Export endpoint ──────────────────────────────────────────────────────────

@router.get(
    "/patients/{patient_id}/export",
    status_code=status.HTTP_200_OK,
    summary="Export patient summary as PDF",
    description="Download a comprehensive patient summary PDF (doctor view)",
)
def export_patient_summary_pdf(
    patient_id: str,
    current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and download a full patient summary PDF for doctor use."""
    from app.models.vitals import Vitals
    from app.utils.pdf_generator import generate_doctor_patient_summary_pdf

    patient = db.query(Patient).filter_by(id=patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    user = db.query(User).filter_by(id=patient.user_id).first()
    doctor_user = db.query(User).filter_by(id=current_user["user_id"]).first()

    patient_name = (user.full_name if user else None) or "Unknown"
    patient_email = (user.email if user else None) or ""
    doctor_name = (doctor_user.full_name if doctor_user else None) or "Doctor"

    vitals_qs = (
        db.query(Vitals)
        .filter_by(patient_id=patient_id)
        .order_by(Vitals.created_at.desc())
        .limit(100)
        .all()
    )
    vitals_data = [
        {
            "heart_rate": v.heart_rate,
            "blood_pressure_systolic": v.blood_pressure_systolic,
            "blood_pressure_diastolic": v.blood_pressure_diastolic,
            "temperature": v.temperature,
            "oxygen_saturation": v.oxygen_saturation,
            "weight": v.weight,
            "respiratory_rate": getattr(v, "respiratory_rate", None),
            "anomaly_detected": v.anomaly_detected,
            "created_at": v.created_at.isoformat() if v.created_at else "",
        }
        for v in vitals_qs
    ]

    # Compute summary inline
    latest_vital = vitals_qs[0] if vitals_qs else None
    latest_status = "UNKNOWN"
    risk_level = "UNKNOWN"
    if latest_vital:
        latest_status = "HIGH" if latest_vital.anomaly_detected else "NORMAL"
        risk_level = "HIGH" if latest_vital.anomaly_detected else "LOW"

    summary = {
        "latest_status": latest_status,
        "risk_level": risk_level,
        "total_messages": db.query(ChatHistory).filter_by(patient_id=patient_id).count(),
        "latest_vital_at": vitals_qs[0].created_at.isoformat() if vitals_qs else None,
    }

    dob = patient.date_of_birth.isoformat() if patient.date_of_birth else None
    pdf_buf = generate_doctor_patient_summary_pdf(
        patient_name=patient_name,
        patient_email=patient_email,
        date_of_birth=dob,
        allergies=patient.allergies,
        current_medications=patient.current_medications,
        medical_history=patient.medical_history,
        emergency_contact=patient.emergency_contact,
        vitals=vitals_data,
        summary=summary,
        doctor_name=doctor_name,
    )

    filename = f"patient_summary_{patient_name.replace(' ', '_')}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Appointment endpoints (doctor side) ──────────────────────────────────────

def _appt_dict(a: Appointment, patient_name: str) -> Dict[str, Any]:
    return {
        "id": a.id,
        "patient_id": a.patient_id,
        "patient_name": patient_name,
        "doctor_user_id": a.doctor_user_id,
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


@router.get("/appointments", summary="List all patient appointment requests")
def list_doctor_appointments(
    status_filter: str | None = None,
    _current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Return all appointments across all patients, optionally filtered by status."""
    query = db.query(Appointment).order_by(Appointment.created_at.desc())
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    appts = query.all()

    patient_ids = {a.patient_id for a in appts}
    patient_names: Dict[str, str] = {}
    for p in db.query(Patient).filter(Patient.id.in_(patient_ids)).all():
        patient_names[p.id] = (p.user.full_name if p.user else "Unknown")

    items = [_appt_dict(a, patient_names.get(a.patient_id, "Unknown")) for a in appts]
    return {"items": items, "total": len(items)}


@router.put("/appointments/{appointment_id}", summary="Update appointment status / schedule")
def update_appointment(
    appointment_id: str,
    body: Dict[str, Any],
    _current_user: dict = Depends(require_role("doctor", "admin")),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Doctor confirms, reschedules, or cancels an appointment request."""
    appt = db.query(Appointment).filter_by(id=appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    allowed_statuses = {"confirmed", "cancelled", "completed", "pending"}
    if "status" in body and body["status"] not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body['status']}")

    if "status" in body:
        appt.status = body["status"]
    if "doctor_notes" in body:
        appt.doctor_notes = body["doctor_notes"]
    if "scheduled_at" in body:
        appt.scheduled_at = body["scheduled_at"]
    if "doctor_user_id" in body:
        appt.doctor_user_id = body["doctor_user_id"]

    db.commit()
    db.refresh(appt)

    patient = db.query(Patient).filter_by(id=appt.patient_id).first()
    patient_name = patient.user.full_name if patient and patient.user else "Unknown"
    return _appt_dict(appt, patient_name)
