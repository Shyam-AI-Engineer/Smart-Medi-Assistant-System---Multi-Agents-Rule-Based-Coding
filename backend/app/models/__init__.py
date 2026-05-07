"""Database models - import all here for easy access."""
from .base import BaseModel
from .user import User, UserRole
from .patient import Patient
from .vitals import Vitals
from .chat_history import ChatHistory
from .medical_report import MedicalReport, ReportStatus
from .medication import Medication
from .doctor_message import DoctorMessage
from .appointment import Appointment
from .audit_log import AuditLog
from .doctor_patient_assignment import DoctorPatientAssignment

__all__ = [
    "BaseModel",
    "User",
    "UserRole",
    "Patient",
    "Vitals",
    "ChatHistory",
    "MedicalReport",
    "ReportStatus",
    "Medication",
    "DoctorMessage",
    "Appointment",
    "AuditLog",
    "DoctorPatientAssignment",
]
