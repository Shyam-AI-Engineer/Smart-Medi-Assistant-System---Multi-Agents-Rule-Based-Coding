"""Doctor ↔ Patient direct message model."""
from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class DoctorMessage(BaseModel):
    """A direct message in a doctor–patient thread.

    sender_role tracks who sent each message so the same table handles
    both doctor→patient notes and patient→doctor replies.
    is_read means the *recipient* has seen it:
      - sender_role="doctor"  → is_read = patient read it
      - sender_role="patient" → is_read = doctor read it
    """

    __tablename__ = "doctor_messages"

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), index=True
    )
    doctor_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    sender_role: Mapped[str] = mapped_column(String(10))  # "doctor" | "patient"
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
