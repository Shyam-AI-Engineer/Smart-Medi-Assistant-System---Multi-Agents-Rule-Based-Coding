"""Request/Response Pydantic schemas for API validation."""
from .chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryQuery,
    ChatHistoryResponse,
    SourceReference,
    ErrorResponse,
)
from .auth_schema import RegisterRequest, LoginRequest, TokenResponse, MeResponse
from .patient_schema import (
    PatientProfileResponse,
    PatientProfileUpdate,
    VitalsCreate,
    VitalsResponse,
    VitalsListResponse,
)

__all__ = [
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatHistoryQuery",
    "ChatHistoryResponse",
    "SourceReference",
    "ErrorResponse",
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "MeResponse",
    # Patient
    "PatientProfileResponse",
    "PatientProfileUpdate",
    "VitalsCreate",
    "VitalsResponse",
    "VitalsListResponse",
]
