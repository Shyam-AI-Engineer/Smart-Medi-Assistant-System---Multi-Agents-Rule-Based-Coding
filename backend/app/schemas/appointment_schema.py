"""Pydantic schemas for appointments."""
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

_VALID_STATUSES = {"confirmed", "cancelled", "completed", "pending"}


class AppointmentRequest(BaseModel):
    reason: str
    preferred_date: Optional[str] = None
    preferred_time_slot: Optional[str] = None
    ai_suggested: bool = False


class AppointmentUpdateRequest(BaseModel):
    status: Optional[str] = None
    doctor_notes: Optional[str] = None
    scheduled_at: Optional[str] = None
    doctor_user_id: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(_VALID_STATUSES)}")
        return v


class AppointmentItem(BaseModel):
    id: str
    patient_id: str
    doctor_user_id: Optional[str] = None
    doctor_name: Optional[str] = None
    reason: str
    preferred_date: Optional[str] = None
    preferred_time_slot: Optional[str] = None
    status: str
    doctor_notes: Optional[str] = None
    scheduled_at: Optional[str] = None
    ai_suggested: bool
    attachment_path: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    items: list[AppointmentItem]
    total: int
