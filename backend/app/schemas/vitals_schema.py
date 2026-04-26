"""Pydantic schemas for vitals storage, trend analysis, and history endpoints."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TrendEnum(str, Enum):
    WORSENING = "WORSENING"
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"


class VitalsStoreRequest(BaseModel):
    """Request to store vitals and receive immediate analysis + trend."""
    patient_id: str = Field(..., description="Patient UUID")
    heart_rate: Optional[float] = Field(None, ge=20, le=300, description="Heart rate in bpm")
    blood_pressure_systolic: Optional[float] = Field(None, ge=50, le=300, description="Systolic BP in mmHg")
    blood_pressure_diastolic: Optional[float] = Field(None, ge=30, le=200, description="Diastolic BP in mmHg")
    oxygen_saturation: Optional[float] = Field(None, ge=50, le=100, description="SpO2 in percent (0-100)")
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0, description="Temperature in Celsius")
    respiratory_rate: Optional[float] = Field(None, ge=4, le=60, description="Respiratory rate in breaths/min")
    weight: Optional[float] = Field(None, ge=1.0, le=500.0, description="Weight in kg")
    notes: Optional[str] = Field(None, max_length=500)

    model_config = {
        "json_schema_extra": {
            "example": {
                "patient_id": "a1b2c3d4-1234-5678-abcd-ef0123456789",
                "heart_rate": 120,
                "blood_pressure_systolic": 150,
                "blood_pressure_diastolic": 95,
                "oxygen_saturation": 92,
                "temperature": 38.3,
            }
        }
    }


class VitalRecordResponse(BaseModel):
    """Stored vitals record (from database)."""
    id: str
    patient_id: str
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    respiratory_rate: Optional[float] = None
    weight: Optional[float] = None
    notes: Optional[str] = None
    anomaly_detected: bool = False
    anomaly_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VitalsStoreResponse(BaseModel):
    """Response from POST /api/v1/vitals/ — includes stored record, AI analysis, and trend."""
    record: VitalRecordResponse
    analysis: dict = Field(..., description="MonitoringAgent analysis result")
    trend: TrendEnum = Field(..., description="Trend compared to recent readings")

    model_config = {
        "json_schema_extra": {
            "example": {
                "record": {
                    "id": "uuid",
                    "patient_id": "uuid",
                    "heart_rate": 120,
                    "created_at": "2026-04-25T10:30:00",
                },
                "analysis": {
                    "overall_status": "HIGH",
                    "severity_level": 3,
                    "should_escalate_to_triage": True,
                },
                "trend": "WORSENING",
            }
        }
    }


class VitalsHistoryItem(BaseModel):
    """Single vitals record in history list."""
    id: str
    heart_rate: Optional[int] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    respiratory_rate: Optional[float] = None
    weight: Optional[float] = None
    notes: Optional[str] = None
    anomaly_detected: bool = False
    anomaly_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VitalsHistoryResponse(BaseModel):
    """Paginated vitals history for a patient."""
    patient_id: str
    items: List[VitalsHistoryItem]
    total: int
    limit: int
    offset: int
    has_next: bool
