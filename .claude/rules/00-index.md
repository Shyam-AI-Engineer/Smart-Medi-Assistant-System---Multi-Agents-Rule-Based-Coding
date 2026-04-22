# Smart Medi Assistant System - Rule Index

> Multi-Agent AI Medical Assistant with Patient Monitoring  
> FastAPI Backend + Next.js Frontend | HIPAA-Ready Architecture | Single-Tenant Hospital System

---

## Core Principles

1. **Clean Architecture** - Strict layer separation (API → Services → Domain → Data Access); dependencies point inward only
2. **Single-Tenant** - No `organization_id` in database; access control via patient_id + RBAC
3. **Type-Safe Everywhere** - Type hints mandatory in Python (3.11+), TypeScript strict mode in frontend
4. **Medical AI Safety** - No hallucinations; agents cite sources; confidence scores required; guardrails on medical content
5. **HIPAA-Ready** - JWT on every request; role-based access control; audit logging on all PHI access; encryption at rest
6. **Production Code Only** - No prototype code; error handling on external calls (OpenAI, database); graceful degradation
7. **Observable** - Structured logging (JSON), metrics on critical paths, tracing on every request
8. **Testable** - ≥80% coverage on critical paths (auth, agents, vital analysis); integration tests on APIs

---

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Framework** | FastAPI 0.104+ (Backend), Next.js 14+ (Frontend) | Modern, type-safe, fast |
| **Language** | Python 3.11+ (Backend), TypeScript 5+ (Frontend) | Strict mode, no any types |
| **Database** | PostgreSQL 16 | ACID, HIPAA-ready, structured data |
| **Cache** | Redis 7+ | Session storage, vitals cache, agent results |
| **Vector DB** | FAISS (local) or Pinecone (cloud) | Medical document embeddings |
| **ORM** | SQLAlchemy 2.0+ | Type hints, async support |
| **Auth** | JWT + OAuth2 | FastAPI native security |
| **AI** | OpenAI API (GPT-4, GPT-4-mini) | Function calling, JSON mode, vision |
| **Testing** | pytest (Backend), Jest (Frontend) | Unit + integration tests |
| **Logging** | structlog + python-json-logger | Structured, JSON format |
| **DevOps** | Docker, docker-compose, GitHub Actions | CI/CD, containerization |
| **Deployment** | Railway (Backend), Vercel (Frontend) | Free tier, auto-scaling |
| **Styling** | Tailwind CSS + shadcn/ui | Component library, accessible |

---

## Rule Files

| # | File | Domain | Status |
|---|------|--------|--------|
| 00 | `00-index.md` | Project overview & principles | ✅ Core |
| 01 | `01-architecture.md` | Layer structure, clean architecture | ⬜ To Create |
| 02 | `02-backend.md` | FastAPI, services, repositories | ⬜ To Create |
| 03 | `03-frontend.md` | Next.js, components, hooks | ⬜ To Create |
| 04 | `04-database.md` | SQLAlchemy models, schema, migrations | ⬜ To Create |
| 05 | `05-authentication.md` | JWT, RBAC, OAuth2, security | ⬜ To Create |
| 06 | `06-agents.md` | 7-agent orchestration, prompts | ⬜ To Create |
| 07 | `07-rag.md` | FAISS, embeddings, RAG pipeline | ⬜ To Create |
| 08 | `08-caching.md` | Redis patterns, cache invalidation | ⬜ To Create |
| 09 | `09-testing.md` | pytest, fixtures, coverage strategy | ⬜ To Create |
| 10 | `10-error-handling.md` | Exceptions, graceful degradation | ⬜ To Create |
| 11 | `11-logging.md` | Structured logging, audit trails | ⬜ To Create |
| 12 | `12-deployment.md` | Docker, Railway, Vercel, environments | ⬜ To Create |
| 13 | `13-api-design.md` | REST conventions, versioning, documentation | ⬜ To Create |
| 14 | `14-medical-safety.md` | Medical content guardrails, disclaimers | ⬜ To Create |
| 15 | `15-hipaa.md` | Compliance, audit logging, data privacy | ⬜ To Create |

---

## User Roles

| Role | Scope | Permissions |
|------|-------|-------------|
| **Patient** | Patient Portal | View own vitals, chat with AI, upload reports, manage appointments |
| **Doctor** | Doctor Dashboard | View assigned patients, review AI analysis, prescribe, conduct telemedicine |
| **Nurse** | Doctor Dashboard | Monitor vitals, triage alerts, assist doctors |
| **Admin** | Admin Panel | Full system access; manage users, devices, audit logs, settings |

---

## AI Agents (7 Specialists)

| Agent | Model | Responsibility | Trigger |
|-------|-------|-----------------|---------|
| **Orchestrator** | GPT-4 | Router: analyzes user intent → dispatches to specialist agents | Every chat message |
| **Clinical Agent** | GPT-4 | Medical knowledge, symptom analysis, differential diagnosis | "I have..." questions |
| **RAG Agent** | GPT-4 | Document retrieval, medical literature synthesis | "Tell me about..." |
| **Triage Agent** | GPT-4-mini | Urgency scoring, escalation decisions | Critical symptom detection |
| **Medication Agent** | GPT-4-mini | Drug interactions, contraindications, warnings | Medication-related queries |
| **Monitoring Agent** | GPT-4-mini | Vital sign trend analysis, anomaly alerts | Real-time vitals ingestion |
| **Follow-up Agent** | GPT-4-mini | Care plan reminders, compliance tracking | Scheduled check-ins |

---

## Database Schema Overview

```
users
├── id (UUID)
├── email (unique)
├── password_hash
├── role (patient | doctor | admin)
├── created_at, updated_at
└── is_active

patients
├── id (UUID)
├── user_id (FK → users)
├── date_of_birth
├── medical_history
├── allergies
├── current_medications
└── emergency_contact

vitals
├── id (UUID)
├── patient_id (FK → patients)
├── heart_rate, blood_pressure, temperature, oxygen_saturation
├── timestamp
└── anomaly_score (if detected)

chat_history
├── id (UUID)
├── patient_id (FK → patients)
├── user_message, ai_response
├── agent_used, confidence_score
└── timestamp

audit_logs
├── id (UUID)
├── user_id (FK → users)
├── action (login, read_patient_data, etc)
├── resource_type
└── timestamp
```

---

## API Endpoint Categories

### Auth (`/api/v1/auth/`)
- POST `/register` - Create account
- POST `/login` - Get JWT token
- POST `/refresh` - Refresh expired token
- GET `/me` - Current user info
- POST `/logout` - Invalidate token (optional)

### Patients (`/api/v1/patients/`)
- GET `/{id}` - Get patient profile
- PUT `/{id}` - Update profile
- GET `/{id}/vitals` - Get vitals history
- GET `/{id}/medical-history` - Get medical records

### Vitals (`/api/v1/vitals/`)
- POST `/` - Record vital signs
- GET `/{patient_id}` - Get vitals history
- WebSocket `/ws/vitals/{patient_id}` - Real-time vitals stream

### Chat (AI) (`/api/v1/chat/`)
- POST `/` - Send message to AI orchestrator
- GET `/history/{patient_id}` - Get conversation history

### Symptoms (`/api/v1/symptoms/`)
- POST `/analyze` - Analyze symptoms via triage agent
- GET `/history/{patient_id}` - Symptom history

### Medications (`/api/v1/medications/`)
- POST `/check-interactions` - Check drug interactions
- GET `/{patient_id}` - Current medications
- POST `/` - Add medication

### Reports (`/api/v1/reports/`)
- POST `/upload` - Upload medical document
- POST `/analyze` - Analyze report with vision agent
- GET `/{patient_id}` - Document history

### Admin (`/api/v1/admin/`)
- GET `/users` - List all users
- GET `/audit-logs` - View audit trail
- GET `/analytics` - System analytics
- PUT `/settings` - Update system configuration

---

## Dependency Injection Pattern

```python
# FastAPI uses Depends() for clean dependency injection

@router.post("/api/v1/chat")
def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),  # JWT validation
    db: Session = Depends(get_db),                    # Database session
    cache = Depends(get_cache),                       # Redis cache
):
    service = ChatService(db, cache)
    return service.handle_message(request, current_user)
```

---

## Folder Structure Summary

```
smart-medi-assistant/
├── .claude/rules/          ← YOU ARE HERE (project guidance)
├── backend/
│   ├── app/
│   │   ├── api/v1/         (FastAPI routes)
│   │   ├── services/       (business logic)
│   │   ├── agents/         (7 AI agents)
│   │   ├── models/         (SQLAlchemy ORM)
│   │   ├── schemas/        (Pydantic validation)
│   │   ├── middleware/     (auth, logging, rate-limit)
│   │   └── utils/          (helpers, JWT, encryption)
│   ├── tests/              (pytest)
│   ├── migrations/         (Alembic)
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── app/                (Next.js routes)
│   ├── components/         (React components)
│   ├── hooks/              (React hooks)
│   ├── lib/                (utilities, API client)
│   ├── types/              (TypeScript types)
│   ├── stores/             (Zustand state)
│   └── package.json
├── docs/                   (Documentation)
├── docker-compose.yml      (Local PostgreSQL + Redis)
└── CLAUDE.md              (Project context)
```

---

## Development Workflow

### Initial Setup
```bash
source venv/Scripts/activate      # Activate virtual environment
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
docker-compose up -d              # PostgreSQL + Redis
python scripts/init_db.py          # Initialize database
```

### Daily Development
```bash
# Terminal 1: Backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
npm run dev

# Terminal 3: Tests (as needed)
pytest -v tests/
```

### Common Commands
```bash
# Backend
pytest tests/ -v --cov=app        # Run tests with coverage
pytest tests/test_auth.py::test_login_success -v  # Run one test
python -m alembic revision --autogenerate -m "msg"  # Create migration
python -m alembic upgrade head    # Apply migrations

# Frontend
npm test                           # Run Jest tests
npm run build                      # Production build
npm run lint                       # Check code style

# Docker
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs -f postgres   # View logs
```

---

## Key Decisions Made

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **FastAPI** over Flask | Modern async, auto-docs, performance | Newer, smaller ecosystem |
| **JWT tokens** | Stateless, scalable, industry-standard | Can't revoke instantly |
| **PostgreSQL** | ACID compliance, structured data, HIPAA | Less flexible schema |
| **SQLAlchemy** | Type hints, relationship management | More verbose than simple SQL |
| **Single-tenant** | Simpler, no org_id overhead | Can't scale to multiple hospitals |
| **OpenAI API** over local LLM | Better quality, no GPU needed | Cost, API dependency |
| **FAISS local** over Pinecone | Free, offline capability | Scalability limited |
| **Next.js + Vercel** | Best DX, edge functions, auto-deploy | Vendor lock-in to Vercel |
| **Tailwind + shadcn** | Fast development, accessible components | CSS-in-JS learning curve |

---

## Before Starting Implementation

**Checklist:**
- [ ] Understand clean architecture (API → Services → Domain)
- [ ] Understand single-tenant access control (no org_id)
- [ ] Understand 7-agent orchestration
- [ ] Understand JWT authentication flow
- [ ] Understand error handling on external calls
- [ ] Virtual environment created
- [ ] Docker/PostgreSQL running locally
- [ ] `.env` files created

---

**Status**: Framework ready  
**Next**: Create detailed rule files (01-15) as needed during development

See individual rule files for implementation details on each layer.
