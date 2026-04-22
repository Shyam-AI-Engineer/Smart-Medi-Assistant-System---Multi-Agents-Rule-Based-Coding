# Database Rules (SQLAlchemy + PostgreSQL)

> Schema design, models, migrations, relationships

---

## SQLAlchemy Setup

### `backend/app/models/base.py`

```python
"""Base model with common audit fields."""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
import uuid

Base = declarative_base()

class BaseModel(Base):
    """All tables inherit from this."""
    __abstract__ = True
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## Model Naming Rules

### Database vs Python

| Database | Python | Example |
|----------|--------|---------|
| `snake_case` table names | `PascalCase` class names | Table: `chat_history` → Class: `ChatHistory` |
| `snake_case` columns | `snake_case` attributes | Column: `blood_pressure_systolic` → `.blood_pressure_systolic` |
| Singular table names | Singular class names | `patients` table → `Patient` class |

---

## Core Models

### User Model

```python
# backend/app/models/user.py
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum
from .base import BaseModel
from werkzeug.security import generate_password_hash, check_password_hash

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    NURSE = "nurse"
    ADMIN = "admin"

class User(BaseModel):
    """User account (patient, doctor, admin)."""
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PATIENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def set_password(self, password: str) -> None:
        """Hash password with bcrypt."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password."""
        return check_password_hash(self.password_hash, password)
```

### Patient Model

```python
# backend/app/models/patient.py
from sqlalchemy import String, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from .base import BaseModel
from .user import User

class Patient(BaseModel):
    """Patient medical profile."""
    __tablename__ = "patients"
    
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, index=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    medical_history: Mapped[str] = mapped_column(Text, nullable=True)
    allergies: Mapped[str] = mapped_column(Text, nullable=True)
    current_medications: Mapped[str] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Relationship: back-populate to User
    user: Mapped[User] = relationship(User, backref="patient_profile")
```

### Vitals Model

```python
# backend/app/models/vitals.py
from sqlalchemy import String, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel

class Vitals(BaseModel):
    """Vital signs measurement."""
    __tablename__ = "vitals"
    
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    
    # Measurements
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=True)  # bpm
    blood_pressure_systolic: Mapped[int] = mapped_column(Integer, nullable=True)  # mmHg
    blood_pressure_diastolic: Mapped[int] = mapped_column(Integer, nullable=True)  # mmHg
    temperature: Mapped[float] = mapped_column(Float, nullable=True)  # Celsius
    oxygen_saturation: Mapped[float] = mapped_column(Float, nullable=True)  # percent (0-100)
    weight: Mapped[float] = mapped_column(Float, nullable=True)  # kg
    
    # Metadata
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    anomaly_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=True)  # 0-1
    
    # Indexes for fast queries
    __table_args__ = (
        Index("ix_vitals_patient_timestamp", "patient_id", "created_at"),
    )
```

### ChatHistory Model

```python
# backend/app/models/chat_history.py
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel

class ChatHistory(BaseModel):
    """Chat message between patient and AI."""
    __tablename__ = "chat_history"
    
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    user_message: Mapped[str] = mapped_column(Text)
    ai_response: Mapped[str] = mapped_column(Text)
    
    # Metadata
    agent_used: Mapped[str] = mapped_column(String(50), default="orchestrator")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.95)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)  # For cost tracking
```

### AuditLog Model

```python
# backend/app/models/audit_log.py
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel

class AuditLog(BaseModel):
    """HIPAA audit trail - log every PHI access."""
    __tablename__ = "audit_logs"
    
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100))  # login, read_vitals, write_medication
    resource_type: Mapped[str] = mapped_column(String(50))  # patient, vitals, report
    resource_id: Mapped[str] = mapped_column(String(36), nullable=True)  # What resource was accessed
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv4/IPv6
    details: Mapped[str] = mapped_column(Text, nullable=True)  # Additional context
    
    __table_args__ = (
        Index("ix_audit_user_timestamp", "user_id", "created_at"),
    )
```

---

## Model Relationships

### One-to-One: User ↔ Patient

```python
# User has one Patient profile
class User(BaseModel):
    __tablename__ = "users"
    # ...
    patient_profile = relationship("Patient", uselist=False, backref="user")

# Patient belongs to one User
class Patient(BaseModel):
    __tablename__ = "patients"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped[User] = relationship(User, backref="patient_profile")

# Usage:
patient = db.query(Patient).filter_by(user_id="123").first()
user = patient.user  # Access user through relationship
```

### One-to-Many: Patient → Vitals

```python
# Patient has many Vitals
class Patient(BaseModel):
    vitals = relationship("Vitals", back_populates="patient")

# Vitals belong to one Patient
class Vitals(BaseModel):
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    patient: Mapped[Patient] = relationship(Patient, back_populates="vitals")

# Usage:
patient = db.query(Patient).get("patient-123")
all_vitals = patient.vitals  # Lazy-loaded relationship
```

---

## Migration Commands

### Create Initial Migration

```bash
cd backend

# Generate migration file (auto-detects changes)
alembic revision --autogenerate -m "initial database schema"

# Review generated file: migrations/versions/xxxx_initial_database_schema.py
# Then apply:
alembic upgrade head
```

### Create New Migration

```bash
# Add column to Patient
# 1. Update model: patient.py

# 2. Create migration
alembic revision --autogenerate -m "add emergency contact to patient"

# 3. Review migration file

# 4. Apply
alembic upgrade head
```

### Downgrade

```bash
# Rollback to previous migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 12345abcde
```

---

## Query Patterns

### Get Single Record

```python
# ✅ CORRECT
patient = db.query(Patient).filter_by(id=patient_id).first()
if not patient:
    raise NotFoundError("Patient not found")

# ❌ WRONG
patient = db.query(Patient).filter_by(id=patient_id).one()  # Raises exception if not found
```

### Get Multiple Records

```python
# ✅ CORRECT - with pagination
skip = (page - 1) * per_page
patients = db.query(Patient).offset(skip).limit(per_page).all()

# ❌ WRONG - no pagination
patients = db.query(Patient).all()  # Loads ALL rows into memory!
```

### Filter with Relationships

```python
# ✅ CORRECT - eager loading
patients = db.query(Patient).join(User).filter(User.is_active == True).all()

# ❌ WRONG - N+1 query problem
patients = db.query(Patient).all()
for patient in patients:
    user = patient.user  # Database query inside loop!
```

### Count Records

```python
total = db.query(Patient).count()
active_count = db.query(Patient).join(User).filter(User.is_active == True).count()
```

---

## Indexes & Performance

### Define Indexes

```python
class Vitals(BaseModel):
    __tablename__ = "vitals"
    
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    
    # Composite index for common query: "Get vitals for patient in time range"
    __table_args__ = (
        Index("ix_vitals_patient_timestamp", "patient_id", "created_at", postgresql_using="btree"),
    )
```

### Common Indexes

```python
# ✅ Index foreign keys
user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)

# ✅ Index search columns
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

# ✅ Composite index for range queries
__table_args__ = (
    Index("ix_patient_created", "patient_id", "created_at"),
)

# ❌ Don't over-index (slows writes)
# Every index has a cost
```

---

## Transaction Management

### Automatic Rollback

```python
def get_db() -> Generator[Session, None, None]:
    """Database session with auto-rollback on error."""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit if no exception
    except Exception:
        db.rollback()  # Rollback on any error
        raise
    finally:
        db.close()
```

### Explicit Rollback

```python
try:
    patient = Patient(...)
    db.add(patient)
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

---

## Type Hints on Models

```python
# ✅ CORRECT
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class Patient(BaseModel):
    medical_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date)

# ❌ WRONG
class Patient(BaseModel):
    medical_history = Column(Text, nullable=True)  # No type hint
    date_of_birth = Column(Date)
```

---

## Summary

- **One model file per table** (no giant models.py file)
- **Relationships**: Use back_populates/backref
- **Indexes**: On foreign keys and search columns
- **Migrations**: Use Alembic for schema changes
- **Type hints**: Mandatory with Mapped[]
- **Audit trail**: Log all PHI access to audit_logs
