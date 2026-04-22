"""Chat history model - conversations between patient and AI."""
from sqlalchemy import String, ForeignKey, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class ChatHistory(BaseModel):
    """Single chat message between patient and AI.

    Stores both user message and AI response.
    Tracks which agent handled the request and confidence.

    Inherits from BaseModel:
    - id: UUID primary key
    - created_at: when message was sent
    - updated_at: when record was modified
    """
    __tablename__ = "chat_history"

    # Foreign key to patient
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id"),  # Link to patients.id
        index=True                  # Fast lookup by patient_id
    )

    # The conversation
    user_message: Mapped[str] = mapped_column(Text)  # What patient typed
    ai_response: Mapped[str] = mapped_column(Text)   # What AI responded

    # Metadata about the response
    agent_used: Mapped[str] = mapped_column(
        String(50),
        default="orchestrator"
    )  # Which agent handled this: orchestrator, clinical, rag, triage, etc.

    confidence_score: Mapped[float] = mapped_column(
        Float,
        default=0.95
    )  # 0-1: how confident AI is in response

    tokens_used: Mapped[int] = mapped_column(
        Integer,
        default=0
    )  # OpenAI API token count (for cost tracking)

    def __repr__(self) -> str:
        return (
            f"<ChatHistory "
            f"patient={self.patient_id} "
            f"agent={self.agent_used} "
            f"confidence={self.confidence_score}>"
        )
