"""Pydantic schemas for patient profile and vitals endpoints."""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


class PatientProfileResponse(BaseModel):
    id: str
    user_id: str
    date_of_birth: Optional[date] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    medical_history: Optional[str] = Field(None, max_length=5000)
    allergies: Optional[str] = Field(None, max_length=2000)
    current_medications: Optional[str] = Field(None, max_length=2000)
    emergency_contact: Optional[str] = Field(None, max_length=255)

    model_config = {
        "json_schema_extra": {
            "example": {
                "date_of_birth": "1990-05-15",
                "allergies": "Penicillin, Aspirin",
                "current_medications": "Metformin 500mg daily",
                "emergency_contact": "Jane Doe: +1-555-0100",
            }
        }
    }


class VitalsCreate(BaseModel):
    heart_rate: Optional[int] = Field(None, ge=20, le=300, description="BPM")
    blood_pressure_systolic: Optional[int] = Field(None, ge=50, le=250, description="mmHg")
    blood_pressure_diastolic: Optional[int] = Field(None, ge=30, le=150, description="mmHg")
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0, description="Celsius")
    oxygen_saturation: Optional[float] = Field(None, ge=50.0, le=100.0, description="Percent")
    weight: Optional[float] = Field(None, ge=1.0, le=500.0, description="Kilograms")
    notes: Optional[str] = Field(None, max_length=500)

    model_config = {
        "json_schema_extra": {
            "example": {
                "heart_rate": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "temperature": 36.5,
                "oxygen_saturation": 98.5,
                "weight": 70.5,
                "notes": "Post-morning walk reading",
            }
        }
    }


class VitalsResponse(BaseModel):
    id: str
    patient_id: str
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    notes: Optional[str] = None
    anomaly_detected: bool = False
    anomaly_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VitalsListResponse(BaseModel):
    items: List[VitalsResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
