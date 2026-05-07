"""Doctor service — patient list, detail, messaging, appointments."""
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, contains_eager

from app.exceptions import ForbiddenError, NotFoundError
from app.models import Patient, User, Vitals, ChatHistory
from app.models.appointment import Appointment
from app.models.doctor_message import DoctorMessage
from app.models.doctor_patient_assignment import DoctorPatientAssignment
from app.schemas.appointment_schema import AppointmentUpdateRequest
from app.schemas.patient_schema import PatientProfileResponse, VitalsResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def classify_vital_risk(vital: Optional[Vitals]) -> Tuple[str, str]:
    """Map a Vitals record → (status, risk_level).

    Returns ("UNKNOWN", "UNKNOWN") when no vital is provided.
    The score thresholds mirror the MonitoringAgent classification.
    """
    if vital is None:
        return "UNKNOWN", "UNKNOWN"
    if not vital.anomaly_detected:
        return "NORMAL", "LOW"
    score = vital.anomaly_score or 0.0
    if score > 0.8:
        return "CRITICAL", "CRITICAL"
    if score > 0.6:
        return "HIGH", "HIGH"
    return "MODERATE", "MODERATE"


def calculate_age(dob: Optional[date]) -> Optional[int]:
    if not dob:
        return None
    today = datetime.utcnow().date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class DoctorService:
    def __init__(self, db: Session):
        self.db = db

    # -----------------------------------------------------------------------
    # Access control
    # -----------------------------------------------------------------------

    def require_patient_access(self, doctor_user_id: str, patient_id: str, role: str) -> None:
        """Raise ForbiddenError if doctor is not assigned to the patient."""
        if role == "admin":
            return
        assigned = (
            self.db.query(DoctorPatientAssignment)
            .filter_by(doctor_user_id=doctor_user_id, patient_id=patient_id)
            .first()
        )
        if not assigned:
            raise ForbiddenError("Not assigned to this patient")

    # -----------------------------------------------------------------------
    # Patient list
    # -----------------------------------------------------------------------

    def list_patients(
        self,
        doctor_user_id: str,
        role: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        if role == "doctor":
            assigned_subq = (
                self.db.query(DoctorPatientAssignment.patient_id)
                .filter(DoctorPatientAssignment.doctor_user_id == doctor_user_id)
                .subquery()
            )
            base_q = self.db.query(Patient).filter(Patient.id.in_(assigned_subq))
        else:
            base_q = self.db.query(Patient)

        total = base_q.count()
        patients = (
            base_q
            .join(User)
            .options(contains_eager(Patient.user))
            .order_by(Patient.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Single query for latest vital per patient (no N+1)
        patient_ids = [p.id for p in patients]
        latest_vital_map: Dict[str, Vitals] = {}
        if patient_ids:
            latest_ts_subq = (
                self.db.query(
                    Vitals.patient_id,
                    func.max(Vitals.created_at).label("max_ts"),
                )
                .filter(Vitals.patient_id.in_(patient_ids))
                .group_by(Vitals.patient_id)
                .subquery()
            )
            latest_vitals = (
                self.db.query(Vitals)
                .join(
                    latest_ts_subq,
                    (Vitals.patient_id == latest_ts_subq.c.patient_id)
                    & (Vitals.created_at == latest_ts_subq.c.max_ts),
                )
                .all()
            )
            latest_vital_map = {v.patient_id: v for v in latest_vitals}

        items = []
        for patient in patients:
            vital = latest_vital_map.get(patient.id)
            status_val, risk_level = classify_vital_risk(vital)
            items.append({
                "id": patient.id,
                "user_id": patient.user_id,
                "full_name": patient.user.full_name if patient.user else "Unknown",
                "age": calculate_age(patient.date_of_birth),
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "latest_vital_status": status_val,
                "risk_level": risk_level,
                "latest_vital_timestamp": vital.created_at.isoformat() if vital else None,
                "latest_vital_id": vital.id if vital else None,
            })

        return {"items": items, "total": total, "limit": limit, "offset": offset,
                "has_next": (offset + limit) < total}

    # -----------------------------------------------------------------------
    # Patient detail
    # -----------------------------------------------------------------------

    def get_patient_detail(
        self,
        patient_id: str,
        doctor_user_id: str,
        role: str,
        vitals_limit: int = 30,
        chat_limit: int = 20,
    ) -> Dict[str, Any]:
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise NotFoundError("Patient not found")

        self.require_patient_access(doctor_user_id, patient_id, role)

        vitals = (
            self.db.query(Vitals)
            .filter(Vitals.patient_id == patient_id)
            .order_by(Vitals.created_at.desc())
            .limit(vitals_limit)
            .all()
        )
        chats = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.patient_id == patient_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(chat_limit)
            .all()
        )

        patient_dict = PatientProfileResponse.model_validate(patient).model_dump()
        patient_dict["user"] = {
            "user_id": patient.user.id,
            "email": patient.user.email,
            "full_name": patient.user.full_name,
        }

        vitals_list = [VitalsResponse.model_validate(v).model_dump() for v in vitals]
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

        latest_status, risk_level = classify_vital_risk(vitals[0] if vitals else None)
        total_messages = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.patient_id == patient_id)
            .count()
        )
        summary = {
            "latest_status": latest_status,
            "risk_level": risk_level,
            "total_messages": total_messages,
            "latest_vital_at": vitals[0].created_at.isoformat() if vitals else None,
        }

        return {
            "patient": patient_dict,
            "vitals": vitals_list,
            "chat_history": chat_list,
            "summary": summary,
        }

    # -----------------------------------------------------------------------
    # Messaging
    # -----------------------------------------------------------------------

    def send_message(
        self,
        patient_id: str,
        doctor_user_id: str,
        role: str,
        body: str,
    ) -> Dict[str, Any]:
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise NotFoundError("Patient not found")
        self.require_patient_access(doctor_user_id, patient_id, role)

        doctor = self.db.query(User).filter(User.id == doctor_user_id).first()
        doctor_name = doctor.full_name if doctor else "Doctor"

        msg = DoctorMessage(
            patient_id=patient_id,
            doctor_user_id=doctor_user_id,
            body=body,
            sender_role="doctor",
            is_read=False,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return _msg_dict(msg, doctor_name)

    def get_thread(
        self,
        patient_id: str,
        doctor_user_id: str,
        role: str,
    ) -> Dict[str, Any]:
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise NotFoundError("Patient not found")
        self.require_patient_access(doctor_user_id, patient_id, role)

        doctor = self.db.query(User).filter(User.id == doctor_user_id).first()
        doctor_name = doctor.full_name if doctor else "Doctor"

        messages = (
            self.db.query(DoctorMessage)
            .filter(
                DoctorMessage.patient_id == patient_id,
                DoctorMessage.doctor_user_id == doctor_user_id,
            )
            .order_by(DoctorMessage.created_at.asc())
            .all()
        )
        # Mark patient replies as read
        for m in messages:
            if m.sender_role == "patient" and not m.is_read:
                m.is_read = True
        self.db.commit()

        return {"items": [_msg_dict(m, doctor_name) for m in messages],
                "total": len(messages), "unread_count": 0}

    def get_unread_count(self, doctor_user_id: str) -> Dict[str, Any]:
        rows = (
            self.db.query(
                DoctorMessage.patient_id,
                func.count(DoctorMessage.id).label("count"),
                User.full_name.label("patient_name"),
            )
            .join(Patient, Patient.id == DoctorMessage.patient_id)
            .join(User, User.id == Patient.user_id)
            .filter(
                DoctorMessage.doctor_user_id == doctor_user_id,
                DoctorMessage.sender_role == "patient",
                DoctorMessage.is_read == False,  # noqa: E712
            )
            .group_by(DoctorMessage.patient_id, User.full_name)
            .all()
        )
        return {
            "total_unread": sum(r.count for r in rows),
            "by_patient": [
                {"patient_id": r.patient_id, "patient_name": r.patient_name, "count": r.count}
                for r in rows
            ],
        }

    # -----------------------------------------------------------------------
    # Appointments
    # -----------------------------------------------------------------------

    def list_appointments(
        self,
        doctor_user_id: str,
        role: str,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = self.db.query(Appointment).order_by(Appointment.created_at.desc())
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        if role == "doctor":
            assigned_subq = (
                self.db.query(DoctorPatientAssignment.patient_id)
                .filter(DoctorPatientAssignment.doctor_user_id == doctor_user_id)
                .subquery()
            )
            query = query.filter(Appointment.patient_id.in_(assigned_subq))

        appts = query.all()
        patient_ids = {a.patient_id for a in appts}
        patient_names: Dict[str, str] = {
            p.id: (p.user.full_name if p.user else "Unknown")
            for p in self.db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
        }
        return {
            "items": [_appt_dict(a, patient_names.get(a.patient_id, "Unknown")) for a in appts],
            "total": len(appts),
        }

    def update_appointment(
        self,
        appointment_id: str,
        doctor_user_id: str,
        role: str,
        update: AppointmentUpdateRequest,
    ) -> Dict[str, Any]:
        appt = self.db.query(Appointment).filter_by(id=appointment_id).first()
        if not appt:
            raise NotFoundError("Appointment not found")
        self.require_patient_access(doctor_user_id, appt.patient_id, role)

        if update.status is not None:
            appt.status = update.status
        if update.doctor_notes is not None:
            appt.doctor_notes = update.doctor_notes
        if update.scheduled_at is not None:
            appt.scheduled_at = update.scheduled_at
        if update.doctor_user_id is not None:
            appt.doctor_user_id = update.doctor_user_id

        self.db.commit()
        self.db.refresh(appt)

        patient = self.db.query(Patient).filter_by(id=appt.patient_id).first()
        patient_name = patient.user.full_name if patient and patient.user else "Unknown"
        return _appt_dict(appt, patient_name)

    # -----------------------------------------------------------------------
    # PDF export data
    # -----------------------------------------------------------------------

    def get_patient_export_data(
        self,
        patient_id: str,
        doctor_user_id: str,
        role: str,
    ) -> Dict[str, Any]:
        patient = self.db.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            raise NotFoundError("Patient not found")
        self.require_patient_access(doctor_user_id, patient_id, role)

        user = self.db.query(User).filter_by(id=patient.user_id).first()
        doctor = self.db.query(User).filter_by(id=doctor_user_id).first()

        vitals_qs = (
            self.db.query(Vitals)
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

        latest_status, risk_level = classify_vital_risk(vitals_qs[0] if vitals_qs else None)
        summary = {
            "latest_status": latest_status,
            "risk_level": risk_level,
            "total_messages": self.db.query(ChatHistory).filter_by(patient_id=patient_id).count(),
            "latest_vital_at": vitals_qs[0].created_at.isoformat() if vitals_qs else None,
        }

        return {
            "patient": patient,
            "patient_name": (user.full_name if user else None) or "Unknown",
            "patient_email": (user.email if user else None) or "",
            "doctor_name": (doctor.full_name if doctor else None) or "Doctor",
            "vitals_data": vitals_data,
            "summary": summary,
        }


# ---------------------------------------------------------------------------
# Private serializers (module-level, shared by service methods)
# ---------------------------------------------------------------------------

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
