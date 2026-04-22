# Smart Medi Assistant System - Architecture

## System Overview

A healthcare AI platform where patients interact with multiple AI agents for medical guidance, vital sign monitoring, and care management.

### What Users Do

**Patients:**
1. Sign up / Login
2. Enter symptoms or health data (vitals)
3. Chat with AI for medical advice
4. View health history and recommendations
5. (Later) Upload medical documents for analysis
6. (Later) Monitor vitals in real-time

**Doctors (Future):**
1. View assigned patients
2. Review AI analysis of patient data
3. Approve/modify AI recommendations
4. Send prescriptions

**Admins (Future):**
1. Manage users and permissions
2. View system analytics
3. Configure system settings

---

## High-Level Architecture

### Layer 1: Frontend (Next.js)
- **What**: User interface for web browsers
- **Tech**: React 18, TypeScript, Tailwind CSS
- **Portals**: 
  - Patient Dashboard (vitals, chat, history)
  - Doctor Dashboard (patient list, review AI analysis)
  - Admin Dashboard (user management, settings)
- **Handles**: UI rendering, form validation, state management

### Layer 2: API Gateway (FastAPI)
- **What**: Processes all requests from frontend
- **Tech**: Python FastAPI (modern async framework)
- **Routes**: `/api/v1/auth`, `/api/v1/patients`, `/api/v1/chat`, etc.
- **Handles**: Request validation, authentication, authorization
- **Returns**: JSON responses

### Layer 3: Business Logic (Services)
- **What**: Core application logic
- **Services**: AuthService, PatientService, ChatService, etc.
- **Handles**: 
  - Processing requests
  - Calling AI agents
  - Interacting with database
  - Caching results

### Layer 4: AI Agents (7 Specialists)
- **What**: Specialized AI models for different medical tasks
- **Tech**: OpenAI API (GPT-4, GPT-4-mini)
- **Orchestrator**: Routes requests to appropriate agent
- **Agents**:
  1. **Clinical Agent** - Medical knowledge questions
  2. **RAG Agent** - Document retrieval & analysis
  3. **Voice Agent** - Speech to text (future)
  4. **Triage Agent** - Assess urgency
  5. **Medication Agent** - Drug interactions
  6. **Monitoring Agent** - Vitals analysis
  7. **Follow-up Agent** - Care reminders

### Layer 5: Data Layer (Database & Cache)
- **PostgreSQL**: Permanent storage (patients, vitals, chat history)
- **Redis**: Fast caching (recent vitals, user sessions)
- **FAISS**: Vector database for medical documents (future)

---

## Data Flow Example: Patient Asks AI

```
1. Patient: "I have a headache and fever"
   ↓
2. Frontend sends POST /api/v1/chat
   {
     "patient_id": "123",
     "message": "I have a headache and fever"
   }
   ↓
3. FastAPI Backend:
   - Validates JWT token
   - Creates ChatHistory entry
   - Calls ChatService
   ↓
4. ChatService:
   - Fetches patient medical history
   - Calls Orchestrator Agent
   ↓
5. Orchestrator Agent:
   - Analyzes: "This is a symptom question"
   - Routes to: Clinical Agent
   ↓
6. Clinical Agent:
   - Uses prompt with medical guidelines
   - Calls OpenAI API with context
   - Gets response: "Headache + fever could be..."
   ↓
7. FastAPI Backend:
   - Saves response to PostgreSQL
   - Caches in Redis
   - Returns to frontend
   ↓
8. Frontend:
   - Displays AI response to patient
   - Shows "Ask Doctor" button
```

---

## Database Schema (Simplified)

```sql
-- Users (Base authentication)
users {
  id (UUID)
  email
  password_hash
  role (patient | doctor | admin)
  created_at
}

-- Patients (Medical profile)
patients {
  id (UUID)
  user_id (FK → users)
  date_of_birth
  medical_history
  allergies
  current_medications
}

-- Vitals (Health measurements)
vitals {
  id (UUID)
  patient_id (FK → patients)
  heart_rate
  blood_pressure
  temperature
  oxygen_saturation
  timestamp
}

-- Chat History
chat_history {
  id (UUID)
  patient_id (FK → patients)
  user_message
  ai_response
  agent_used (clinical | rag | etc)
  timestamp
}

-- Audit Log (Security)
audit_logs {
  id (UUID)
  user_id
  action (read_patient_data, login, etc)
  resource_type
  timestamp
}
```

---

## API Endpoints Overview

### Authentication
```
POST   /api/v1/auth/register   - Create account
POST   /api/v1/auth/login      - Get JWT token
POST   /api/v1/auth/refresh    - Refresh token
GET    /api/v1/auth/me         - Current user info
```

### Patients
```
GET    /api/v1/patients/{id}   - Get patient profile
PUT    /api/v1/patients/{id}   - Update profile
GET    /api/v1/patients/{id}/vitals  - Get vitals history
```

### Chat (AI)
```
POST   /api/v1/chat            - Send message to AI
GET    /api/v1/chat/history/{patient_id} - Get chat history
```

### Vitals
```
POST   /api/v1/vitals          - Record vital signs
GET    /api/v1/vitals/{patient_id} - Get vitals
```

### Health (Operations)
```
GET    /api/v1/health/ready    - Is system ready?
GET    /api/v1/health/live     - Is system running?
```

---

## Security Architecture

### Authentication Flow
```
User enters credentials
         ↓
Backend hashes password
         ↓
Check against database
         ↓
If valid: Generate JWT token
         ↓
Return token to frontend
         ↓
Frontend stores token (secure cookie)
         ↓
Frontend includes token in every request
         ↓
Backend validates token on each request
```

### Access Control
```
Patient requesting: GET /api/v1/vitals/123
         ↓
Backend checks: Is this patient the logged-in user?
         ↓
If YES: Return data
If NO: Return 403 Forbidden
```

### Secrets Management
```
.env file (LOCAL ONLY):
- OPENAI_API_KEY
- DATABASE_URL
- JWT_SECRET
- REDIS_URL

Production (Never in code):
- Use environment variables
- Use secrets manager (AWS Secrets, etc)
- Rotate regularly
```

---

## Caching Strategy

### What Gets Cached?
1. **User sessions** (in Redis) - Expires in 24h
2. **Recent vitals** (in Redis) - Expires in 1h
3. **AI responses** (in Redis) - Expires in 24h
4. **Patient profiles** (in Redis) - Expires in 6h

### Cache Hit Example
```
Patient asks: "What's my average heart rate?"
         ↓
Backend checks Redis cache
         ↓
Found? → Return cached result (fast!)
Not found? → Query database, save to cache
```

---

## Agent System Architecture

### Orchestrator Agent (Router)
```python
def route_request(user_message: str):
    intent = classify_intent(user_message)
    # "What's my heart rate?" → clinical_agent
    # "Upload my lab report" → rag_agent
    # "Is aspirin safe with my meds?" → medication_agent
    return specialized_agent
```

### Agent Pattern
```python
class BaseAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
    
    def execute(self, prompt: str):
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a medical assistant..."},
                {"role": "user", "content": prompt}
            ]
        )
        return response

class ClinicalAgent(BaseAgent):
    def execute(self, patient_symptoms: str):
        # Add medical knowledge to prompt
        prompt = f"Patient symptoms: {patient_symptoms}. Analyze based on..."
        return super().execute(prompt)
```

---

## Deployment Architecture (Future)

```
┌─ Vercel (Frontend) ──→ smart-medi-frontend.vercel.app
│
├─ Railway/Render (Backend) ──→ api.smart-medi.app
│  ├── FastAPI app
│  ├── Celery workers (background jobs)
│  └── Health checks
│
└─ External Services
   ├── PostgreSQL (Managed DB)
   ├── Redis (Cache layer)
   ├── OpenAI API (GPT-4)
   └── Pinecone (Vector DB - optional)
```

---

## Key Design Decisions

| Decision | Why | Trade-off |
|----------|-----|-----------|
| Single-tenant | Simpler, no org_id overhead | Can't scale to multiple hospitals easily (future refactor) |
| FastAPI over Flask | Modern, async, auto-docs, performance | Steeper learning curve |
| JWT tokens | Stateless, scalable | Can't revoke instantly (use blacklist for logout) |
| PostgreSQL over NoSQL | Structured data, ACID, medical compliance | Less flexible schema |
| OpenAI API over local LLM | Better quality, no GPU needed | Higher cost, API dependency |
| FAISS local over Pinecone | Free, offline | Limited to local docs (Pinecone as upgrade) |

---

## Error Handling Strategy

Every API endpoint should:
1. Validate input (Pydantic)
2. Try to process
3. Catch specific exceptions
4. Return meaningful error to user

```python
@router.post("/api/v1/chat")
def chat(message: ChatSchema):
    try:
        # Validate patient exists
        patient = db.session.query(Patient).filter_by(id=message.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Try to get AI response
        response = orchestrator_agent.execute(message.text)
        return {"response": response}
    
    except OpenAIError as e:
        logger.error(f"OpenAI failed: {e}")
        return {"response": "AI service temporarily unavailable. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"response": "An error occurred. Please contact support."}
```

---

## Next: Implementation Steps

This architecture will be built incrementally:
1. Phase 1: Foundation (auth, database, basic CRUD)
2. Phase 2: AI Agents (orchestrator, clinical agent)
3. Phase 3: Advanced agents (RAG, voice, triage)
4. Phase 4: Deployment

See `docs/STEP_BY_STEP.md` for detailed implementation steps.
