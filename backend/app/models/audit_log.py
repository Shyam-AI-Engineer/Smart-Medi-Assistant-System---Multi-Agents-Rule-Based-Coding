"""AuditLog model — HIPAA-ready access trail for every PHI operation."""
from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from .base import BaseModel


class AuditLog(BaseModel):
    """Immutable record of who accessed or modified patient data and when.

    Every row is written once and never updated. Compliance officers use these
    rows to answer: who touched patient X's record, and when?

    Inherits from BaseModel: id (UUID PK), created_at, updated_at.
    """
    __tablename__ = "audit_logs"

    # Actor — denormalised so logs stay readable after users are deleted
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[str] = mapped_column(String(50), nullable=False)

    # What happened
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. login | register | view_patient | view_vitals | record_vitals
    #       send_chat | view_chat_history | export_pdf | view_audit_logs

    # What was touched
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # e.g. auth | patient | vitals | chat | admin
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Outcome
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    # success | failure

    # Network context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Optional free-text — e.g. failure reason, number of records returned
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        # Fast range queries: "all events for user X in the last 30 days"
        Index("ix_audit_user_created", "user_id", "created_at"),
        # Fast action filter: "all login events"
        Index("ix_audit_action_created", "action", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_email} @ {self.created_at}>"
