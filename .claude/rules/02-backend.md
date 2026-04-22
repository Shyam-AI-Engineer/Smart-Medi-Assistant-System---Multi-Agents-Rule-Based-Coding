# Backend Rules (FastAPI + Services)

> FastAPI routes, services, error handling, async patterns

---

## FastAPI Project Setup

### App Factory Pattern

**`backend/app/__init__.py`**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.extensions import engine
from app.models import BaseModel

def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    app = FastAPI(
        title="Smart Medi Assistant API",
        version="0.1.0",
        description="Multi-agent AI medical assistant",
    )
    
    # CORS - Allow frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create tables on startup
    BaseModel.metadata.create_all(bind=engine)
    
    # Include routers
    from app.api.v1 import api_router
    app.include_router(api_router)
    
    return app

app = create_app()
```

**`backend/app/main.py`**:
```python
from app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## API Route Organization

### File Structure
```
api/v1/
├── __init__.py          (router aggregation)
├── auth.py              (200 lines max)
├── patients.py          (200 lines max)
├── chat.py              (200 lines max)
├── vitals.py
├── medications.py
└── reports.py
```

### __init__.py Pattern
```python
from fastapi import APIRouter
from .auth import router as auth_router
from .patients import router as patients_router
from .chat import router as chat_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(chat_router)

__all__ = ["api_router"]
```

---

## Route Definition Rules

### Required Elements

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import ChatRequest, ChatResponse
from app.services import ChatService
from app.middleware.auth_middleware import get_current_user
from app.extensions import get_db

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse, status_code=201)
def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI.
    
    - **message**: Patient message (required)
    - **patient_id**: Patient ID (from JWT user)
    
    Returns AI response.
    """
    service = ChatService(db)
    response = service.handle_message(request.message, current_user["id"])
    return ChatResponse(response=response)
```

**Requirements:**
- ✅ Router with prefix and tags
- ✅ Type hints on all parameters
- ✅ response_model specified
- ✅ status_code specified
- ✅ Docstring with params
- ✅ Dependencies for auth & database
- ✅ Service injection via Depends()

---

## Pydantic Schemas

### Request/Response Models

**`backend/app/schemas/chat_schema.py`**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """User message to AI."""
    message: str = Field(..., min_length=1, max_length=1000)
    patient_id: Optional[str] = None  # From JWT
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I have a headache and fever"
            }
        }

class ChatResponse(BaseModel):
    """AI response."""
    response: str
    agent_used: str = "orchestrator"
    confidence_score: float = 0.95
    timestamp: str
```

**Rules:**
- ✅ One schema per file
- ✅ Use Field() for validation
- ✅ Type hints mandatory
- ✅ Config with JSON schema examples
- ❌ Never use `Any` type

---

## Error Handling

### Exception Hierarchy

```python
# backend/app/exceptions.py
class MediAssistantException(Exception):
    """Base exception."""
    pass

class ValidationError(MediAssistantException):
    """User input validation failed."""
    pass

class NotFoundError(MediAssistantException):
    """Resource not found."""
    pass

class UnauthorizedError(MediAssistantException):
    """User not authenticated."""
    pass

class ForbiddenError(MediAssistantException):
    """User not authorized for resource."""
    pass

class ExternalServiceError(MediAssistantException):
    """External API failed (OpenAI, etc)."""
    pass
```

### Error Handling in Routes

```python
@router.post("/api/v1/chat")
def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        service = ChatService(db)
        response = service.handle_message(request.message, current_user["id"])
        return {"response": response}
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except UnauthorizedError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    except ExternalServiceError as e:
        logger.error(f"External service failed: {e}")
        # Don't expose details to user
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again."
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Rules:**
- ✅ Catch specific exceptions first
- ✅ Log all errors
- ✅ Don't expose internal details to users
- ✅ Return appropriate HTTP status codes
- ✅ Include exc_info=True for unexpected errors

---

## Dependency Injection

### Get Current User

```python
# backend/app/middleware/auth_middleware.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from app.utils.jwt_utils import verify_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
) -> dict:
    """Validate JWT and return user info."""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }

def require_role(role: str):
    """Dependency to enforce role."""
    def check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return check
```

### Usage in Routes

```python
@router.get("/api/v1/admin/users")
def list_users(
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin-only endpoint."""
    users = db.query(User).all()
    return users
```

---

## Database Session Management

### get_db Dependency

```python
# backend/app/extensions.py
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit successful transactions
    except Exception:
        db.rollback()  # Rollback on error
        raise
    finally:
        db.close()
```

**Usage:**
```python
@router.get("/api/v1/patients/{id}")
def get_patient(
    id: str,
    db: Session = Depends(get_db),  # Auto-managed by FastAPI
):
    patient = db.query(Patient).filter_by(id=id).first()
    return patient
```

---

## Response Models

### Standardized Responses

```python
# backend/app/schemas/response_schema.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    """Standard API response."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None

class PaginatedResponse(BaseModel):
    """Paginated response."""
    items: list
    total: int
    page: int
    per_page: int
    has_next: bool
```

**Usage:**
```python
@router.get("/api/v1/patients")
def list_patients(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(Patient)
    total = query.count()
    items = query.offset((page-1)*per_page).limit(per_page).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_next=page * per_page < total,
    )
```

---

## Type Hints (Mandatory)

```python
# ✅ CORRECT
from typing import Optional, List
from app.models import Patient

def get_patient(
    patient_id: str,
    db: Session,
) -> Optional[Patient]:
    """Get patient by ID."""
    return db.query(Patient).filter_by(id=patient_id).first()

def list_patients(db: Session) -> List[Patient]:
    """Get all patients."""
    return db.query(Patient).all()

# ❌ WRONG
def get_patient(patient_id, db):  # No type hints
    return db.query(Patient).filter_by(id=patient_id).first()

def list_patients(db) -> list:  # Generic list, not List[Patient]
    return db.query(Patient).all()
```

---

## Logging

```python
import structlog
logger = structlog.get_logger()

@router.post("/api/v1/chat")
def send_message(request: ChatRequest, current_user: dict):
    logger.info("chat.message.received", user_id=current_user["id"])
    
    try:
        response = service.handle_message(request.message, current_user["id"])
        logger.info("chat.message.sent", user_id=current_user["id"], agent="orchestrator")
        return response
    except Exception as e:
        logger.error("chat.message.failed", user_id=current_user["id"], error=str(e))
        raise
```

---

## Summary

- **Routes**: Thin; max 200 lines
- **Error Handling**: Catch specific exceptions; graceful degradation
- **Dependencies**: Inject via Depends(); no globals
- **Schemas**: Pydantic for validation
- **Type Hints**: Mandatory everywhere
- **Logging**: Structured, contextual
