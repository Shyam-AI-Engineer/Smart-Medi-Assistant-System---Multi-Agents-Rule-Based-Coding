# Clean Architecture Rules

> Strict layer separation; dependencies point inward only

---

## Layer Hierarchy

```
┌─────────────────────────────────────┐
│    Presentation Layer               │
│  (Next.js Components, Pages)        │
├─────────────────────────────────────┤
│    API Gateway Layer                │
│  (FastAPI Routes, Request/Response) │
├─────────────────────────────────────┤
│    Application Services Layer       │
│  (Use cases, orchestration)         │
├─────────────────────────────────────┤
│    Domain Layer                     │
│  (Business logic, entities, rules)  │
├─────────────────────────────────────┤
│    Data Access Layer                │
│  (Repository interfaces)            │
├─────────────────────────────────────┤
│    Infrastructure Layer             │
│  (PostgreSQL, Redis, OpenAI API)    │
└─────────────────────────────────────┘
```

---

## Dependency Rule

**Dependencies MUST point inward only.**

```
✅ ALLOWED:
- Presentation → API Gateway
- API Gateway → Services
- Services → Domain
- Domain → (nothing, pure logic)
- Services → Data Access
- Data Access → Infrastructure

❌ FORBIDDEN:
- Domain → Services (domain rules depend on services)
- Presentation → Services (skip API gateway)
- Presentation → Data Access (skip both layers)
- Infrastructure → Domain (database classes in models)
```

---

## Layer Responsibilities

### 1. Presentation Layer (Frontend: Next.js)
**What**: User interface

**Files**:
- `frontend/app/*/page.tsx` - Page components
- `frontend/components/` - UI components
- `frontend/hooks/` - Custom React hooks
- `frontend/stores/` - Zustand state management

**Responsibilities**:
- ✅ Render UI
- ✅ Collect user input
- ✅ Display API responses
- ✅ Route navigation
- ✅ Client state management

**Must NOT**:
- ❌ Make direct database queries
- ❌ Contain business logic
- ❌ Call external APIs directly (go through Backend API)

**Example**:
```typescript
// ✅ CORRECT
export default function PatientDashboard() {
  const { patient, isLoading } = usePatient();  // Hook → API
  return <div>{patient?.name}</div>;
}

// ❌ WRONG
export default function PatientDashboard() {
  const [patient, setPatient] = useState(null);
  useEffect(() => {
    // Direct API call without hook abstraction
    fetch('http://api/patients/' + id).then(...)
  }, []);
}
```

---

### 2. API Gateway Layer (Backend: FastAPI Routes)
**What**: HTTP request/response interface

**Files**:
- `backend/app/api/v1/*.py` - Route files (auth.py, patients.py, chat.py, etc.)

**Responsibilities**:
- ✅ Accept HTTP requests
- ✅ Validate input (Pydantic schemas)
- ✅ Extract JWT token, validate user
- ✅ Call services
- ✅ Format responses (200, 201, 400, 401, 403, 500)
- ✅ Return JSON

**Must NOT**:
- ❌ Contain business logic (belongs in Services)
- ❌ Access database directly (belongs in Services)
- ❌ Make AI API calls directly (belongs in Services)

**Example**:
```python
# ✅ CORRECT
@router.post("/api/v1/chat")
def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate input ✅
    # Get user from token ✅
    # Delegate to service ✅
    service = ChatService(db)
    response = service.handle_message(request.message, current_user["id"])
    return {"response": response}

# ❌ WRONG
@router.post("/api/v1/chat")
def chat(request: ChatRequest):
    # Business logic in route
    patient = db.query(Patient).filter_by(...).first()
    response = openai.ChatCompletion.create(...)  # AI call in route!
    return {"response": response}
```

**File Size Limit**: 200 lines max
- If >200 lines: Split into sub-routers in separate files

---

### 3. Application Services Layer
**What**: Business logic orchestration

**Files**:
- `backend/app/services/auth_service.py`
- `backend/app/services/patient_service.py`
- `backend/app/services/chat_service.py`
- `backend/app/services/ai_service.py` - OpenAI wrapper
- etc.

**Responsibilities**:
- ✅ Implement use cases (register, login, send chat message)
- ✅ Call domain logic
- ✅ Call repositories/data access
- ✅ Call external services (OpenAI, agents)
- ✅ Handle errors, retry logic
- ✅ Caching decisions

**Must NOT**:
- ❌ Accept HTTP requests (Routes do that)
- ❌ Return HTTP responses
- ❌ Validate HTTP input (Routes validate)
- ❌ Import Flask/FastAPI decorators

**Example**:
```python
# ✅ CORRECT
class ChatService:
    def __init__(self, db: Session, cache):
        self.db = db
        self.cache = cache
        self.ai_service = AIService()
    
    def handle_message(self, message: str, user_id: str) -> str:
        # 1. Get patient
        patient = self.db.query(Patient).filter_by(user_id=user_id).first()
        
        # 2. Try cache first
        cache_key = f"chat:{user_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # 3. Call AI
        try:
            response = self.ai_service.get_clinical_response(message, patient)
        except Exception as e:
            logger.error(f"AI failed: {e}")
            return "AI service temporarily unavailable."
        
        # 4. Cache result
        self.cache.set(cache_key, response, ex=3600)
        
        # 5. Save to database
        chat = ChatHistory(patient_id=patient.id, user_message=message, ai_response=response)
        self.db.add(chat)
        self.db.commit()
        
        return response
```

**File Size Limit**: 300 lines max
- If >300 lines: Extract sub-services

---

### 4. Domain Layer
**What**: Pure business rules (no frameworks)

**Files**:
- `backend/app/models/patient.py` - Entity definition
- `backend/app/agents/base_agent.py` - Domain logic for agents

**Responsibilities**:
- ✅ Define entities (Patient, Vitals, User)
- ✅ Define business rules (validation, calculations)
- ✅ Define interfaces (repositories, services)

**Must NOT**:
- ❌ Import database libraries (SQLAlchemy stays in models but minimal)
- ❌ Import FastAPI
- ❌ Call external APIs
- ❌ Know about HTTP

**Example**:
```python
# ✅ CORRECT - Pure domain logic
class Patient:
    def __init__(self, id: str, name: str, age: int, medical_history: str):
        self.id = id
        self.name = name
        self.age = age
        self.medical_history = medical_history
    
    def is_high_risk(self) -> bool:
        """Business rule: Patient is high-risk if age > 65 and has history"""
        return self.age > 65 and len(self.medical_history) > 0

# ❌ WRONG - Domain logic in API layer
@router.get("/api/v1/patients/{id}")
def get_patient(id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).get(id)
    if patient.age > 65 and patient.medical_history:  # Business logic!
        return {"high_risk": True}
```

---

### 5. Data Access Layer
**What**: Repository interfaces for database queries

**Files**:
- `backend/app/models/*.py` - SQLAlchemy ORM models
- `backend/app/utils/db.py` - Database utilities

**Responsibilities**:
- ✅ Define data models (SQLAlchemy)
- ✅ Provide data access methods via repositories
- ✅ Handle database transactions
- ✅ Migrations (Alembic)

**Must NOT**:
- ❌ Contain business logic
- ❌ Return HTTP responses

---

### 6. Infrastructure Layer
**What**: External systems

**Technologies**:
- PostgreSQL database
- Redis cache
- OpenAI API
- FAISS vector database

---

## Data Flow Example

**User sends chat message:**

```
1. Next.js Component (Presentation)
   └─ Calls API: POST /api/v1/chat { message: "I have headache" }

2. FastAPI Route (API Gateway) - auth.py
   ├─ Validates JWT token ✅
   ├─ Validates Pydantic schema ✅
   └─ Calls ChatService

3. ChatService (Services)
   ├─ Fetches patient from repository
   ├─ Checks cache (Redis)
   ├─ Calls OrchestrationAgent
   └─ Saves result to database

4. OrchestrationAgent (Domain)
   ├─ Analyzes intent: "Symptom question"
   ├─ Routes to ClinicalAgent
   └─ Returns medical advice

5. FastAPI Route returns response
   └─ Next.js Component displays answer

Response goes back through same layers.
```

---

## File Organization Rules

### Backend
```
api/v1/auth.py            (max 200 lines, auth routes only)
services/auth_service.py  (max 300 lines, login/register logic)
models/user.py            (max 150 lines, one model per file)
agents/base_agent.py      (max 300 lines, agent base class)
```

### Frontend
```
app/(auth)/login/page.tsx          (max 250 lines)
components/forms/LoginForm.tsx     (max 250 lines)
hooks/useAuth.ts                   (max 100 lines)
```

---

## Testing Strategy

**Each layer tested independently:**

```
Unit Tests:
- Domain logic: Patient.is_high_risk()
- Services: ChatService.handle_message()

Integration Tests:
- Routes: POST /api/v1/auth/login

End-to-End Tests:
- Frontend: User logs in, sees dashboard
```

---

## Common Violations

| Violation | ❌ Wrong | ✅ Correct |
|-----------|---------|----------|
| Business logic in routes | `POST /chat` contains AI call | Extract to ChatService |
| Routes access DB directly | `@router.get()` does `db.query()` | Use service dependency |
| Domain imports framework | `from fastapi import ...` in models | Models are framework-agnostic |
| Frontend skips API | Component calls `fetch()` directly | Use hooks that abstract API |
| Circular imports | A depends on B, B depends on A | Inject dependencies |
| Giants files | 500+ line service file | Split into focused services |

---

## Summary

**Remember**: Each layer has one job.

- **Presentation**: What users see
- **API**: How frontend talks to backend
- **Services**: What the app does
- **Domain**: Business rules
- **Data Access**: How to get data
- **Infrastructure**: External systems

**Dependency Rule**: Outer → Inner only (never reverse)
