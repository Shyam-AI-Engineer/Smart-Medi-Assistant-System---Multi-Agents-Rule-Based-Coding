"""Vitals model - vital signs measurements from patients."""
from sqlalchemy import String, Float, ForeignKey, Integer, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class Vitals(BaseModel):
    """Vital signs measurement for a patient.

    Records: heart rate, blood pressure, temperature, oxygen saturation, weight
    Can detect anomalies automatically.

    Inherits from BaseModel:
    - id: UUID primary key
    - created_at: when measurement was taken (can be queried for time-series)
    - updated_at: when record was modified
    """
    __tablename__ = "vitals"

    # Foreign key to patient
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id"),  # Link to patients.id
        index=True                  # Fast lookup by patient_id
    )

    # Vital sign measurements
    heart_rate: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )  # BPM (beats per minute)

    blood_pressure_systolic: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )  # mmHg (millimeters of mercury)

    blood_pressure_diastolic: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )  # mmHg

    temperature: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )  # Celsius

    oxygen_saturation: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )  # Percent (0-100%)

    weight: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )  # Kilograms

    # Metadata
    notes: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )  # Additional notes

    anomaly_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )  # Monitoring agent sets this if abnormal

    anomaly_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )  # 0-1 score of how abnormal (0=normal, 1=very abnormal)

    # Composite index for common query pattern:
    # "Get all vitals for patient X in time range Y"
    __table_args__ = (
        Index("ix_vitals_patient_timestamp", "patient_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Vitals HR={self.heart_rate} "
            f"BP={self.blood_pressure_systolic}/{self.blood_pressure_diastolic} "
            f"patient={self.patient_id}>"
        )
