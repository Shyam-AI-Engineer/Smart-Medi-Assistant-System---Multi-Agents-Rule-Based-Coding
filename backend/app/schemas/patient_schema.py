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


# ======================== Vitals Analysis Schemas ========================


class PatientInfoRequest(BaseModel):
    """Optional patient context for vitals analysis."""
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age in years")
    medical_history: Optional[str] = Field(None, max_length=500, description="Medical conditions")
    current_medications: Optional[str] = Field(None, max_length=500, description="Current medications")

    model_config = {
        "json_schema_extra": {
            "example": {
                "age": 65,
                "medical_history": "Hypertension, Type 2 Diabetes",
                "current_medications": "Metformin, Lisinopril",
            }
        }
    }


class VitalsAnalyzeRequest(BaseModel):
    """Request to analyze vital signs."""
    heart_rate: Optional[float] = Field(None, ge=20, le=300, description="Heart rate in bpm")
    blood_pressure_systolic: Optional[float] = Field(None, ge=50, le=300, description="Systolic BP in mmHg")
    blood_pressure_diastolic: Optional[float] = Field(None, ge=30, le=200, description="Diastolic BP in mmHg")
    oxygen_saturation: Optional[float] = Field(None, ge=50, le=100, description="SpO2 in percent (0-100)")
    temperature: Optional[float] = Field(None, ge=30.0, le=45.0, description="Temperature in Celsius")
    respiratory_rate: Optional[float] = Field(None, ge=4, le=60, description="Respiratory rate in breaths/min")
    patient_info: Optional[PatientInfoRequest] = Field(None, description="Optional patient context")

    model_config = {
        "json_schema_extra": {
            "example": {
                "heart_rate": 145,
                "blood_pressure_systolic": 155,
                "blood_pressure_diastolic": 98,
                "oxygen_saturation": 96,
                "temperature": 38.5,
                "respiratory_rate": 22,
                "patient_info": {
                    "age": 65,
                    "medical_history": "Hypertension",
                    "current_medications": "Lisinopril",
                }
            }
        }
    }


class VitalAnalysisItem(BaseModel):
    """Analysis result for a single vital sign."""
    vital_type: str = Field(..., description="Type of vital (e.g., heart_rate)")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement (e.g., bpm, mmHg, %)")
    status: str = Field(..., description="Status (NORMAL, ELEVATED, HIGH, CRITICAL_LOW, CRITICAL_HIGH)")
    severity: str = Field(..., description="Severity level (NORMAL, MODERATE, HIGH, CRITICAL)")
    normal_range: dict = Field(..., description="Normal range {min, max}")
    explanation: str = Field(..., description="Medical explanation of the vital")
    recommendation: str = Field(..., description="Recommended action")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")

    model_config = {"from_attributes": True}


class VitalsAnalyzeResponse(BaseModel):
    """Response from vital signs analysis."""
    overall_status: str = Field(..., description="Overall status: NORMAL, MODERATE, HIGH, CRITICAL")
    severity_level: int = Field(..., ge=1, le=4, description="Severity level 1-4 (1=NORMAL, 4=CRITICAL)")
    vital_analyses: List[VitalAnalysisItem] = Field(..., description="Analysis for each vital")
    critical_findings: List[str] = Field(..., description="List of critical findings")
    overall_assessment: str = Field(..., description="Overall health assessment")
    recommendations: List[str] = Field(..., description="Recommended actions")
    should_escalate_to_triage: bool = Field(..., description="Whether to escalate to triage")
    confidence_score: float = Field(..., ge=0, le=1, description="Overall confidence score")
    agent_used: str = Field(default="monitoring", description="Agent used for analysis")
    tokens_used: int = Field(default=0, description="Tokens used in API calls")
    timestamp: str = Field(..., description="ISO timestamp of analysis")
    disclaimer: str = Field(..., description="Medical disclaimer")
    response: str = Field(..., description="Patient-friendly formatted response")
    error: bool = Field(default=False, description="Whether an error occurred")

    model_config = {
        "json_schema_extra": {
            "example": {
                "overall_status": "HIGH",
                "severity_level": 3,
                "vital_analyses": [
                    {
                        "vital_type": "heart_rate",
                        "value": 145,
                        "unit": "bpm",
                        "status": "HIGH",
                        "severity": "HIGH",
                        "normal_range": {"min": 60, "max": 100},
                        "explanation": "Elevated heart rate...",
                        "recommendation": "Contact doctor immediately",
                        "confidence": 0.93,
                    }
                ],
                "critical_findings": ["heart_rate: HIGH"],
                "overall_assessment": "Your vital signs indicate elevated readings...",
                "recommendations": ["Contact healthcare provider immediately"],
                "should_escalate_to_triage": True,
                "confidence_score": 0.93,
                "agent_used": "monitoring",
                "tokens_used": 450,
                "timestamp": "2026-04-25T10:30:00.000Z",
                "disclaimer": "⚠️ **DISCLAIMER**: This is not a substitute...",
                "response": "⚠️ **VITAL SIGNS ANALYSIS**...",
                "error": False,
            }
        }
    }
