"""Base model with common audit fields (created_at, updated_at, id)."""
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
import uuid

Base = declarative_base()

class BaseModel(Base):
    """All database tables inherit from this.

    Provides:
    - id (UUID primary key)
    - created_at (when record was created)
    - updated_at (when record was last modified)
    """
    __abstract__ = True  # Don't create a table for this

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid.uuid4())  # Auto-generate UUID
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow  # Automatically set on creation
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow  # Automatically update on each change
    )
