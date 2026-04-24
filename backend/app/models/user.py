"""User model - accounts for patients, doctors, and admins."""
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from .base import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash


class UserRole(str, enum.Enum):
    """User roles in the system."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class User(BaseModel):
    """User account - base for all system users.

    Can be:
    - Patient: sees own vitals, chats with AI
    - Doctor: sees assigned patients, reviews AI analysis
    - Admin: full system access

    Inherits from BaseModel:
    - id: UUID primary key
    - created_at: when account was created
    - updated_at: when last modified
    """
    __tablename__ = "users"

    # Basic info
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,  # No duplicate emails
        index=True    # Fast lookup by email
    )
    password_hash: Mapped[str] = mapped_column(String(255))  # Never store plaintext!
    full_name: Mapped[str] = mapped_column(String(255))

    # Role & status
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.PATIENT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship to Patient profile (one-to-one)
    patient_profile: Mapped["Patient"] = relationship("Patient", back_populates="user", uselist=False)

    def set_password(self, password: str) -> None:
        """Hash password with bcrypt before storing.

        Usage:
            user = User(email="john@example.com", full_name="John Doe")
            user.set_password("SecurePassword123")  # Hashes it
            db.add(user)
            db.commit()
        """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password: str) -> bool:
        """Verify password against hash.

        Usage:
            if user.check_password("SecurePassword123"):
                print("Login successful!")
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
