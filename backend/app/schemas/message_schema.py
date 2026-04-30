"""Pydantic schemas for doctor–patient direct messaging."""
from pydantic import BaseModel, Field


class MessageOut(BaseModel):
    id: str
    patient_id: str
    doctor_user_id: str
    doctor_name: str
    body: str
    sender_role: str  # "doctor" | "patient"
    is_read: bool
    created_at: str

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageOut]
    total: int
    unread_count: int


class SendMessageRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


class ReplyRequest(BaseModel):
    doctor_user_id: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1, max_length=2000)
