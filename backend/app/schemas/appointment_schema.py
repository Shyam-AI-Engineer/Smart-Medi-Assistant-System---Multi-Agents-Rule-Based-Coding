"""Pydantic schemas for appointments."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AppointmentRequest(BaseModel):
    reason: str
    preferred_date: Optional[str] = None
    preferred_time_slot: Optional[str] = None
    ai_suggested: bool = False


class AppointmentUpdateRequest(BaseModel):
    status: str
    doctor_notes: Optional[str] = None
    scheduled_at: Optional[str] = None
    doctor_user_id: Optional[str] = None


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
