# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Smart Medi Assistant System - Overview

A multi-agent AI medical assistant platform that helps patients get medical guidance, monitor vitals, and manage care plans. Built by a beginner developer with progressive, step-by-step implementation.

### Tech Stack
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Next.js 14+ with TypeScript
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Vector DB**: FAISS (local) or Pinecone (optional cloud)
- **AI**: OpenAI API (GPT-4, GPT-4-mini, Whisper)
- **Environment**: Python virtual environment (./venv)

### Multi-Agent System (7 Agents)
1. **Clinical Agent** - Medical knowledge queries
2. **RAG Agent** - Document retrieval & analysis
3. **Voice Agent** - Speech-to-text processing
4. **Triage Agent** - Patient urgency assessment
5. **Medication Agent** - Drug interaction checking
6. **Monitoring Agent** - Vital sign analysis
7. **Orchestrator Agent** - Dispatcher/router

---

## Virtual Environment Setup

**ALWAYS work within the activated venv**

```bash
# Activate (Windows - bash)
source venv/Scripts/activate

# Activate (Mac/Linux)
source venv/bin/activate

# Deactivate (when done)
deactivate
```

---

## Project Structure (Beginner Version)

```
smart-medi-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py                 # FastAPI app creation
│   │   ├── main.py                     # Entry point
│   │   ├── config.py                   # Config, env variables
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py             # Login, register endpoints
│   │   │       ├── patients.py         # Patient CRUD endpoints
│   │   │       ├── vitals.py           # Vitals tracking endpoints
│   │   │       ├── chat.py             # AI chat endpoints
│   │   │       ├── voice.py            # Voice endpoints (later)
│   │   │       └── health.py           # Health check
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py           # Abstract base agent
│   │   │   ├── orchestrator.py         # Agent dispatcher
│   │   │   ├── clinical_agent.py       # Medical knowledge
│   │   │   ├── rag_agent.py            # RAG queries
│   │   │   ├── triage_agent.py         # Urgency assessment
│   │   │   ├── medication_agent.py     # Drug interactions
│   │   │   └── prompts.py              # All agent prompts
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User model (base)
│   │   │   ├── patient.py              # Patient model
│   │   │   ├── vitals.py               # Vitals model
│   │   │   └── chat_history.py         # Chat history model
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py         # Auth logic
│   │   │   ├── patient_service.py      # Patient operations
│   │   │   ├── vitals_service.py       # Vitals operations
│   │   │   ├── ai_service.py           # OpenAI API wrapper
│   │   │   └── rag_service.py          # RAG/FAISS operations
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth_schema.py          # Pydantic schemas
│   │   │   ├── patient_schema.py
│   │   │   └── vitals_schema.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth_middleware.py      # JWT validation
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── db.py                   # Database utilities
│   │   │   └── jwt_utils.py            # JWT helpers
│   │   └── extensions.py               # Database, Redis, etc.
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_patients.py
│   │   └── test_agents.py
│   ├── migrations/                     # Alembic migrations (later)
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Example env file
│   └── main.py                         # WSGI entry point
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                  # Root layout
│   │   ├── page.tsx                    # Landing page
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── register/
│   │   │       └── page.tsx
│   │   └── (patient)/
│   │       ├── dashboard/
│   │       │   └── page.tsx
│   │       ├── vitals/
│   │       │   └── page.tsx
│   │       ├── chat/
│   │       │   └── page.tsx
│   │       └── layout.tsx              # Patient layout
│   ├── components/
│   │   ├── ui/                         # Button, Input, Card, etc.
│   │   ├── forms/                      # Login, Register, Vitals forms
│   │   ├── charts/                     # Vitals charts
│   │   └── layout/                     # Navbar, Sidebar
│   ├── lib/
│   │   ├── api.ts                      # API client (fetch wrapper)
│   │   ├── auth.ts                     # NextAuth config
│   │   └── utils.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useApi.ts
│   ├── types/
│   │   ├── api.ts
│   │   └── models.ts
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── .env.example
│
├── docs/
│   ├── ARCHITECTURE.md                 # System design
│   ├── API.md                          # API endpoints
│   ├── DATABASE.md                     # Schema reference
│   ├── DEPLOYMENT.md                   # Deployment guide
│   └── STEP_BY_STEP.md                 # Implementation steps
│
├── .env.example                        # Root env example
├── docker-compose.yml                  # Local development
├── README.md
└── CLAUDE.md                           # This file

```

---

## Development Workflow (Beginner Steps)

### Step 1: Install Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (in separate terminal)
cd frontend
npm install
```

### Step 2: Start Local Services (PostgreSQL, Redis)
```bash
# From project root
docker-compose up -d
```

### Step 3: Run Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
# API available at: http://localhost:8000
```

### Step 4: Run Frontend
```bash
cd frontend
npm run dev
# App available at: http://localhost:3000
```

### Step 5: Run Tests
```bash
# Backend tests
cd backend
pytest -v

# Frontend tests (in separate terminal)
cd frontend
npm test
```

### Step 6: Run Single Test (Debugging)
```bash
# Run one test file
pytest tests/test_auth.py -v

# Run one specific test
pytest tests/test_auth.py::test_login_success -v

# With print statements visible
pytest tests/test_auth.py -v -s
```

---

## Architecture Overview (Beginner Friendly)

```
┌──────────────────────────┐
│    Browser (Next.js)     │
│  Patient Dashboard       │
└────────────┬─────────────┘
             │ HTTP/JSON
             ▼
┌──────────────────────────────────────┐
│     FastAPI Backend                  │
│  ├── /api/v1/auth                    │
│  ├── /api/v1/patients                │
│  ├── /api/v1/vitals                  │
│  └── /api/v1/chat (AI)               │
└────────────┬──────────────────────────┘
             │
    ┌────────┼────────┬────────┐
    ▼        ▼        ▼        ▼
┌────────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│ Agents │ │  DB  │ │Redis │ │OpenAI API│
│ (7x)   │ │(PG)  │ │Cache │ │(GPT-4)   │
└────────┘ └──────┘ └──────┘ └──────────┘
```

**How it works:**
1. User logs in via Next.js frontend
2. Frontend sends API request to FastAPI backend
3. Backend authenticates (JWT token)
4. For AI requests, backend dispatches to **Orchestrator Agent**
5. Orchestrator routes to specialized agents (Clinical, RAG, Medication, etc.)
6. Agents call OpenAI API with medical prompts
7. Results cached in Redis, stored in PostgreSQL
8. Frontend displays response

---

## Important: Access Control & Security

**Single-tenant system** - No multi-organization support. Access control:

```python
# Patient can see only their own vitals
@router.get("/api/v1/vitals/{patient_id}")
def get_vitals(patient_id: str, current_user = Depends(get_current_user)):
    # Check: is this the logged-in patient?
    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # ... fetch vitals
```

**Key security rules:**
- ✅ JWT token on every request
- ✅ Role-based access (patient, doctor, admin)
- ✅ Validate all user input with Pydantic
- ✅ Never expose passwords or API keys
- ✅ Use environment variables for secrets (.env file)

---

## Common Commands Cheat Sheet

```bash
# Activate venv (ALWAYS first!)
source venv/Scripts/activate

# Install new package
pip install <package_name>
pip freeze > requirements.txt

# Run backend with auto-reload
python -m uvicorn app.main:app --reload

# Run all tests
pytest -v

# Run tests with coverage
pytest --cov=app tests/

# Format code (Python)
black .

# Lint code (Python)
flake8 .

# Generate Alembic migration (later)
alembic revision --autogenerate -m "description"
alembic upgrade head

# Database shell
psql -U postgres -d smart_medi_dev
```

---

## Implementation Approach

### Phase 1: Foundation (What We'll Start With)
- ✅ Project structure
- ✅ Database models (User, Patient, Vitals)
- ✅ Authentication (JWT)
- ✅ Basic API endpoints (auth, patients CRUD)
- ✅ Basic frontend (login, dashboard)

### Phase 2: AI Integration (Next)
- Orchestrator Agent setup
- Clinical Agent integration
- Chat endpoint
- Frontend chat UI

### Phase 3: Advanced Features (Later)
- RAG with FAISS
- Voice agent (Whisper)
- Real-time vitals monitoring
- Medication interaction checking
- Triage & urgency assessment

### Phase 4: Deployment (Final)
- Docker containerization
- Railway/Render deployment
- Vercel frontend hosting

---

## Debugging Tips

**Common Errors & Fixes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | Package not installed | Run `pip install -r requirements.txt` |
| `JWT token invalid` | Token expired or wrong | Login again |
| `Database connection error` | PostgreSQL not running | Run `docker-compose up -d` |
| `CORS error` | Frontend/backend domain mismatch | Check CORS middleware in FastAPI |
| `OpenAI API error` | Invalid API key | Check `.env` file has valid `OPENAI_API_KEY` |

---

## Next Steps

1. ✅ Understand this structure
2. ➡️ **Confirm you're ready** (respond with "Ready" or ask questions)
3. Create folder structure
4. Create `.env` files
5. Install dependencies
6. Create database models
7. Build first API endpoint

**What's next: Step 1 - Create the project folder structure**

Ready to proceed? Confirm and I'll walk you through the first implementation step!
