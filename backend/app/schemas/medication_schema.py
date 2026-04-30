"""Pydantic schemas for medications."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime


class MedicationRequest(BaseModel):
    medication_name: str = Field(..., max_length=255)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class MedicationResponse(BaseModel):
    id: str
    medication_name: str
    dosage: str
    frequency: str
    start_date: date
    end_date: Optional[date]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MedicationsListResponse(BaseModel):
    items: List[MedicationResponse]
    total: int


class InteractionCheckResponse(BaseModel):
    risk_level: str
    interactions: List[Any]
    contraindications: List[str]
    warning_signs: List[str]
    patient_response: str
    disclaimer: str
    confidence_score: float
