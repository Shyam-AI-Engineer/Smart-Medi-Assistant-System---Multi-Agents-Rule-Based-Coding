"""Patient model - medical profile linked to User."""
from sqlalchemy import String, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from .base import BaseModel
from .user import User


class Patient(BaseModel):
    """Patient medical profile.

    Links to User account (one-to-one relationship).
    Contains medical history and current health information.

    Inherits from BaseModel:
    - id: UUID primary key
    - created_at: when patient record was created
    - updated_at: when last modified
    """
    __tablename__ = "patients"

    # Foreign key to users table
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),  # Link to users.id
        unique=True,             # One patient per user
        index=True               # Fast lookup by user_id
    )

    # Personal info
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)

    # Medical history (text fields for now, could be structured later)
    medical_history: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default=""
    )
    allergies: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default=""
    )
    current_medications: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default=""
    )
    emergency_contact: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    # Relationship back to User
    user: Mapped[User] = relationship(User, back_populates="patient_profile")

    def __repr__(self) -> str:
        return f"<Patient {self.user_id} - {self.user.full_name if self.user else 'Unknown'}>"
