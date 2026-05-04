"""Appointment request model — patient requests, doctor confirms."""
from sqlalchemy import String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class Appointment(BaseModel):
    """An appointment request submitted by a patient.

    status lifecycle:
      pending   → doctor hasn't acted yet
      confirmed → doctor set a scheduled_at datetime
      cancelled → patient or doctor cancelled
      completed → appointment occurred
    """

    __tablename__ = "appointments"

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), index=True
    )
    doctor_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    preferred_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_time_slot: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    doctor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_suggested: Mapped[bool] = mapped_column(default=False)
    attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
