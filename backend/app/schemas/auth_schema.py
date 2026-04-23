"""Pydantic schemas for auth endpoints (register, login, refresh, me)."""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "patient@example.com",
                "password": "SecurePass123",
                "full_name": "John Doe",
            }
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "patient@example.com",
                "password": "SecurePass123",
            }
        }
    }


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "uuid-here",
                "email": "patient@example.com",
                "role": "patient",
            }
        }
    }


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "uuid-here",
                "email": "patient@example.com",
                "full_name": "John Doe",
                "role": "patient",
                "is_active": True,
                "created_at": "2026-04-23T10:00:00",
            }
        }
    }
