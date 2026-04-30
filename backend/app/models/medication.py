"""Medication model - patient medication records."""
from typing import Optional
from sqlalchemy import String, ForeignKey, Index, Date
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from .base import BaseModel


class Medication(BaseModel):
    """A medication a patient is currently taking or has taken."""
    __tablename__ = "medications"

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), index=True
    )
    medication_name: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str] = mapped_column(String(100))
    frequency: Mapped[str] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_medications_patient_startdate", "patient_id", "start_date"),
    )

    def __repr__(self) -> str:
        return f"<Medication {self.medication_name} {self.dosage} patient={self.patient_id}>"
