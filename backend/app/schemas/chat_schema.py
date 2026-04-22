"""Chat request/response schemas for API validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Patient message to medical AI."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Patient's message (1-1000 chars)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I have a headache and fever for 2 days"
            }
        }


class SourceReference(BaseModel):
    """Reference to a medical document source."""
    file: str = Field(..., description="Source file name or title")
    relevance: str = Field(..., description="Relevance score as percentage (e.g., '92%')")
    source_type: str = Field(default="text", description="Type: text, pdf, image, video, audio")
    preview: Optional[str] = Field(
        default=None,
        description="Brief preview of relevant content"
    )


class ChatResponse(BaseModel):
    """AI response to patient message."""
    response: str = Field(..., description="Medical response with disclaimer")
    sources: List[SourceReference] = Field(
        default=[],
        description="Retrieved documents used in response"
    )
    agent_used: str = Field(
        default="orchestrator",
        description="Which agent handled this: orchestrator, clinical, rag, medication, triage"
    )
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in response (0-1)"
    )
    tokens_used: int = Field(
        default=0,
        description="Tokens consumed (for cost tracking)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When response was generated"
    )
    context_documents_used: int = Field(
        default=0,
        description="Number of FAISS documents retrieved"
    )
    error: Optional[bool] = Field(
        default=False,
        description="Whether response represents an error"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on medical guidelines, a headache with fever may indicate viral infection such as flu or cold. Symptoms typically resolve in 3-7 days. Seek immediate care if you experience severe headache, stiff neck, or difficulty breathing.\n\nRECOMMENDED: Rest, fluids, fever management with acetaminophen or ibuprofen (unless contraindicated). Monitor temperature. This is for informational purposes only.",
                "sources": [
                    {
                        "file": "headache_diagnosis.pdf",
                        "relevance": "94%",
                        "source_type": "pdf",
                        "preview": "Differential diagnosis of headache with fever..."
                    },
                    {
                        "file": "viral_infections_guide.txt",
                        "relevance": "89%",
                        "source_type": "text"
                    }
                ],
                "agent_used": "clinical",
                "confidence_score": 0.92,
                "tokens_used": 450,
                "context_documents_used": 2,
                "error": False
            }
        }


class ChatHistoryQuery(BaseModel):
    """Query for retrieving chat history."""
    patient_id: str = Field(..., description="Patient ID to retrieve history for")
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Max messages to return (1-100)"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Skip N messages (for pagination)"
    )


class ChatHistoryResponse(BaseModel):
    """Chat history list response."""
    items: List[Dict[str, Any]] = Field(
        default=[],
        description="Chat messages"
    )
    total: int = Field(default=0, description="Total messages for patient")
    limit: int = Field(default=20, description="Requested limit")
    offset: int = Field(default=0, description="Requested offset")
    has_next: bool = Field(default=False, description="Whether more messages exist")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message (user-friendly)")
    detail: Optional[str] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When error occurred"
    )
