"""Doctor-Patient assignment — controls which doctors can access which patients."""
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class DoctorPatientAssignment(BaseModel):
    """One row = one doctor is assigned to one patient.

    Access rule: a doctor may only view/message/export a patient they appear in
    this table for. Admins bypass the check entirely.
    Created by admins via POST /api/v1/admin/assignments.
    """
    __tablename__ = "doctor_patient_assignments"

    doctor_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), index=True, nullable=False
    )
    assigned_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("doctor_user_id", "patient_id", name="uq_doctor_patient"),
    )
