import enum
from typing import Optional
from sqlalchemy import String, Integer, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class ReportStatus(str, enum.Enum):
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class MedicalReport(BaseModel):
    """Patient-uploaded medical report (lab results, discharge summary, etc)."""

    __tablename__ = "medical_reports"

    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20))  # "pdf" | "docx" | "txt"
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus), default=ReportStatus.PROCESSING
    )
    faiss_doc_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    text_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
