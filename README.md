# Smart Medi Assistant System

> **Production-Grade Multi-Agent AI Medical Assistant**  
> FastAPI Backend + Next.js Frontend | HIPAA-Ready Security | Single-Tenant Architecture  
> *Advanced AI-driven clinical decision support with real-time vitals monitoring*

---

## 🎯 System Overview

Smart Medi Assistant is an enterprise medical AI platform that helps patients get immediate medical guidance, monitor vital signs, and manage care plans through a conversational AI interface. Built with clean architecture principles, it demonstrates professional-grade patterns for medical software.

**Key Capabilities:**
- 🤖 **7-Agent AI System** — Specialized agents for clinical, triage, medication, RAG, and monitoring
- 📊 **Vital Sign Monitoring** — Real-time tracking with anomaly detection
- 💬 **Conversational AI** — Natural language chat with confidence scoring
- 📋 **Audit Trail** — HIPAA-compliant logging of all PHI access
- 🔐 **Security-First** — JWT auth, token revocation, error boundaries
- 🏥 **Medical Safety** — Hallucination detection, confidence thresholds, disclaimers

---

## 🏗️ Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Next.js Frontend (Vercel)                  │
│        Patient Portal | Doctor Dashboard | Admin Panel       │
│  - Real-time vitals display                                 │
│  - Chat interface with streaming responses                  │
│  - Error boundaries (no blank screens)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS/JSON
                           ▼
┌──────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Railway)                       │
│                                                              │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐   │
│  │   API Routes │  │  Services  │  │    Middleware    │   │
│  │ (Auth, Chat, │  │ (Business  │  │ (Auth, Rate-    │   │
│  │  Vitals)     │  │ Logic)     │  │  Limit, Audit)   │   │
│  └──────────────┘  └────────────┘  └──────────────────┘   │
│           ↓                ↓                ↓                │
│  ┌───────────────────────────────────────────────────┐     │
│  │         Agent Orchestration Layer                 │     │
│  │  ┌──────────┬──────────┬──────────┐ ┌──────────┐ │     │
│  │  │Clinical  │RAG Agent │ Triage   │ │Medication│ │     │
│  │  │Agent     │(FAISS)   │ Agent    │ │ Agent    │ │     │
│  │  └──────────┴──────────┴──────────┘ └──────────┘ │     │
│  │  Orchestrator → Routes intent to specialists    │     │
│  └───────────────────────────────────────────────────┘     │
│           ↓              ↓              ↓                    │
└───────────┼──────────────┼──────────────┼──────────────────┘
            │              │              │
    ┌───────┴──────┬───────┴──────┬──────┴────────┐
    ▼              ▼              ▼               ▼
┌─────────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐
│ Euri API    │ │PostgreSQL│ │ Redis  │ │ FAISS Index  │
│(GPT-4o-mini)│ │(RDS)     │ │(Cache) │ │(Vectors)     │
└─────────────┘ └──────────┘ └────────┘ └──────────────┘
```

### Data Flow: Chat Message → Response

```
1. User Types Message (Frontend)
           ↓
2. POST /api/v1/chat (FastAPI Route)
   - Validates JWT token ✅
   - Checks token revocation ✅
   - Validates input (Pydantic)
           ↓
3. ChatService (Business Logic)
   - Orchestrator analyzes intent
   - Routes to ClinicalAgent
           ↓
4. ClinicalAgent (RAG Pipeline)
   - Embed query (Euri)
   - Search FAISS index (top-k documents)
   - Assemble context from medical docs
           ↓
5. LLM Generation (Euri API)
   - Call GPT-4o-mini with context
   - Apply safety guardrails (0.65 confidence threshold)
           ↓
6. Database & Audit
   - Save to ChatHistory table
   - Log to AuditLog (user_id, action, ip_address)
   - Cache result in Redis
           ↓
7. Response to Frontend
   - HTTP 200 with response + sources + confidence
   - Front shows sources, confidence, agent name
```

---

## 🛠️ Tech Stack

### Backend
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | 0.104+ | Modern async HTTP server |
| **Language** | Python | 3.11+ | Type hints, async/await |
| **Database** | PostgreSQL | 16 | ACID transactions, structured data |
| **ORM** | SQLAlchemy | 2.0+ | Type-safe data access |
| **Cache** | Redis | 7+ | Session storage, result caching |
| **Vector DB** | FAISS | Local | Medical document embeddings |
| **Auth** | JWT/OAuth2 | FastAPI native | Stateless authentication |
| **AI/LLM** | Euri API | GPT-4o-mini | Medical response generation |
| **Embeddings** | Euri API | Gemini Embedding 2 (768d) | Document similarity search |
| **Testing** | pytest | 9.0+ | Unit & integration tests |
| **Rate Limiting** | SlowAPI | Latest | DDoS protection |

### Frontend
| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | Next.js | 14+ | React + server components |
| **Language** | TypeScript | 5+ | Type safety, strict mode |
| **Styling** | Tailwind CSS | Latest | Utility-first CSS |
| **Components** | shadcn/ui | Latest | Accessible UI components |
| **State** | Zustand | Latest | Lightweight state management |
| **Data Fetching** | TanStack Query | v5+ | Server state management |
| **Testing** | Jest | Latest | Unit tests |
| **Linting** | ESLint | Latest | Code quality |

### DevOps & Deployment
| Component | Platform | Purpose |
|-----------|----------|---------|
| **Backend Hosting** | Railway | Deploy FastAPI containers |
| **Frontend Hosting** | Vercel | Deploy Next.js globally |
| **Database** | Railway PostgreSQL | Managed database |
| **Cache** | Railway Redis | Managed cache |
| **Containerization** | Docker | Local & production |
| **Version Control** | Git | Source code history |

---

## 🔐 Security Features

### Authentication & Authorization
- **JWT Tokens** — 30-minute access + 7-day refresh with automatic revocation
- **Token Revocation** — Logout immediately invalidates tokens via Redis revocation list
- **RBAC** — Role-based access control (patient, doctor, admin)
- **Password Security** — bcrypt hashing with salt, minimum 8 characters

### Data Protection
- **HIPAA Audit Trail** — Every patient data access logged (user_id, action, ip_address, timestamp)
- **Single-Tenant** — No multi-org vulnerability; patient only sees own data
- **Secrets Management** — API keys in environment variables, never in code
- **TLS/HTTPS** — All traffic encrypted in transit

### Error Handling & Safety
- **Error Boundaries** — 5 frontend error.tsx files prevent blank screens
- **Hallucination Prevention** — 0.65 confidence threshold for medical advice
- **Medical Disclaimers** — All AI responses include legal disclaimers
- **Graceful Degradation** — Services degrade rather than crash (Euri down → use cache)

### Medical AI Safety
| Feature | Implementation |
|---------|----------------|
| **Hallucination Guard** | FAISS similarity threshold 0.65 minimum |
| **Confidence Scoring** | All responses include 0.0-1.0 confidence |
| **Source Citations** | Medical advice links to source documents |
| **Medication Safety** | Limited 7-drug database (not comprehensive) |
| **Triage Escalation** | Critical symptoms routed to emergency |

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Backend Tests** | 24+ passing (auth, chat, audit, revocation) |
| **Frontend Components** | 20+ reusable React components |
| **API Endpoints** | 25+ REST endpoints |
| **Database Tables** | 6 (users, patients, vitals, chat_history, audit_logs, reports) |
| **AI Agents** | 7 specialized agents (orchestrator, clinical, RAG, triage, medication, monitoring, follow-up) |
| **Documentation Files** | 8 (architecture, API, database, auth, dev security, env vars, error boundaries) |
| **Lines of Code** | 8,000+ (backend + frontend) |
| **Error Boundary Coverage** | 5 route segments protected |

---

## 🚀 Deployment Flow

### Development (Local)
```bash
1. source venv/Scripts/activate        # Activate environment
2. docker-compose up -d                # Start PostgreSQL + Redis
3. cd backend && uvicorn app.main:app  # Start backend (port 8000)
4. cd frontend && npm run dev          # Start frontend (port 3000)
```

### Production (Railway + Vercel)

#### Backend Deployment (Railway)
```
1. Push to main branch
   ↓
2. Railway detects changes
   ↓
3. Build Docker image (Dockerfile)
   ↓
4. Run database migrations (Alembic)
   ↓
5. Deploy to Railway dyno
   ↓
6. Verify health check (GET /health)
   ↓
7. Route traffic to new version
```

#### Frontend Deployment (Vercel)
```
1. Push to main branch
   ↓
2. Vercel detects changes
   ↓
3. Run npm install
   ↓
4. Run npm run build
   ↓
5. Deploy to Vercel edge network
   ↓
6. Assign production URL
   ↓
7. CDN caches static assets globally
```

### Environment Configuration
```
Development:  .env (local, never committed)
Production:   Railway + Vercel dashboards (secrets managers)

DATABASE_URL  → Railway PostgreSQL add-on
REDIS_URL     → Railway Redis add-on
JWT_SECRET    → Generated locally, unique per environment
EURI_API_KEY  → From Euri dashboard
```

---

## 📚 Documentation Files

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | This file — project overview | ✅ |
| `CLAUDE.md` | AI assistant guidance | ✅ |
| `ENVIRONMENT_VARIABLES.md` | Env var setup & secrets | ✅ |
| `DEVELOPER_SECURITY.md` | Security best practices | ✅ |
| `ERROR_BOUNDARIES.md` | Frontend error handling | ✅ |
| `.claude/rules/00-index.md` | Core principles & tech stack | ✅ |
| `.claude/rules/01-architecture.md` | Clean architecture layers | ✅ |
| `.claude/rules/02-backend.md` | FastAPI patterns | ✅ |
| `.claude/rules/04-database.md` | SQLAlchemy models | ✅ |
| `.claude/rules/05-authentication.md` | JWT & RBAC | ✅ |
| `.claude/rules/06-euri-faiss-architecture.md` | AI & RAG system | ✅ |
| `.claude/rules/07-euri-error-handling.md` | Error handling patterns | ✅ |

---

## 💡 Lessons Learned

### What Went Well ✅
1. **Clean Architecture** — Layer separation made adding features easy
2. **Error Boundaries** — Prevented blank screens, improved UX
3. **Audit Logging** — HIPAA trail essential for medical compliance
4. **Type Safety** — FastAPI + TypeScript caught bugs early
5. **Token Revocation** — Redis-backed revocation list lightweight & effective
6. **Graceful Degradation** — System stays up even when external APIs fail

### Challenges Overcome 🛠️
1. **AI Hallucinations** — Solved with 0.65 similarity threshold
2. **Token Expiry Mismatch** — Fixed by tying revocation TTL to token expiry
3. **Test Fixture Bugs** — Conftest client fixture needed explicit db.commit()
4. **FAISS Scalability** — 1M+ vectors need pre-indexing strategy
5. **CORS Issues** — Railway URLs require dynamic CORS configuration

### Architectural Wins 🏆
1. **Single-Tenant Model** — No org_id overhead, simpler access control
2. **Dependency Injection** — FastAPI Depends() made testing trivial
3. **Service Layer** — Business logic isolated from HTTP layer
4. **Redis TTL** — Automatic cleanup of revoked tokens without cronjobs

### Future Improvements 🚀
1. **Sentry Integration** — Real-time error tracking in production
2. **Pre-commit Hooks** — Automated secret detection (implemented ✅)
3. **Refresh Token Rotation** — Token reuse detection for extra security
4. **API Rate Limiting** — Per-user rates to prevent abuse (SlowAPI in place ✅)
5. **Database Connection Pooling** — Optimize for high concurrency (configured ✅)

### Medical Safety Lessons 📋
1. **Disclaimers Required** — All AI advice must include legal disclaimers
2. **Confidence Thresholds** — Don't give medical advice on uncertain matches
3. **Audit Trails Critical** — Every access needs logging for liability
4. **Escalation Paths** — Emergency symptoms must route to triage
5. **Medication Databases** — Never ship with incomplete drug databases

---

## ✅ Quality Metrics

### Test Coverage
- **Backend**: 24+ passing tests (auth, chat, audit, token revocation)
- **Frontend**: Error boundary tests for all route segments
- **Integration**: End-to-end tests for auth flow, token revocation

### Code Quality
- **Type Hints**: 100% on critical paths (routes, services)
- **Error Handling**: Specific exceptions with graceful fallbacks
- **Documentation**: Every module has docstrings
- **Pre-commit Hooks**: Automatic secret detection blocks leaks

### Security Posture
- ✅ No hardcoded secrets (environment variables only)
- ✅ No SQL injection (SQLAlchemy ORM)
- ✅ No XSS (React escaping + CSP headers)
- ✅ No CSRF (JWT token validation)
- ✅ HIPAA audit trail (write_audit() on all PHI access)

---

## 🎓 Quick Learning Path

**For Portfolio Review (30 min):**
1. Read this README
2. Review architecture diagram
3. Check `ENVIRONMENT_VARIABLES.md` (secrets handling)
4. Skim `DEVELOPER_SECURITY.md` (security practices)

**For Deep Technical Dive (2 hours):**
1. Read `.claude/rules/00-index.md` (overview)
2. Read `.claude/rules/01-architecture.md` (clean architecture)
3. Read `backend/app/middleware/auth_middleware.py` (token revocation)
4. Review `backend/tests/test_auth.py` (5 revocation tests)
5. Check `frontend/components/error/ErrorBoundaryFallback.tsx` (error handling)

**For Implementation (ongoing):**
- `.claude/rules/` folder has detailed patterns
- `DEVELOPER_SECURITY.md` has setup instructions
- `ENVIRONMENT_VARIABLES.md` explains all config

---

## 🤝 Development Workflow

### Standard Commit Flow
```bash
git add file.py              # Stage changes
git commit -m "type: message"  # Pre-commit hook runs
# ✅ Hook passes → commit succeeds
# ❌ Hook fails → check for secrets
```

### Pre-Commit Hook Examples

✅ **Allowed:**
```bash
git commit -m "feat: add new endpoint"
# Changes: new route, service logic, tests
# Pre-commit: ✅ passes (no secrets)
```

❌ **Blocked:**
```bash
git add .env
git commit -m "add env file"
# Pre-commit: ❌ BLOCKS (.env is forbidden)
# Message: "File matching pattern '\.env$' is staged"
```

---

## 📈 Next Steps for This Project

1. **Immediate**: Run locally following Quick Start
2. **Short-term**: Add more medical document sources to FAISS
3. **Medium-term**: Integrate with hospital EHR system
4. **Long-term**: Deploy to BAA-eligible infrastructure for HIPAA compliance

---

## 📞 Support & Resources

**Documentation:**
- Architecture questions → `.claude/rules/01-architecture.md`
- Backend implementation → `.claude/rules/02-backend.md`
- Database schema → `.claude/rules/04-database.md`
- Authentication → `.claude/rules/05-authentication.md`
- Security setup → `DEVELOPER_SECURITY.md`
- Deployments → `ENVIRONMENT_VARIABLES.md`

**External Links:**
- FastAPI Docs: https://fastapi.tiangolo.com/
- Next.js Docs: https://nextjs.org/docs
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- JWT Reference: https://jwt.io/introduction

---

## 🎯 Status

**Profile Project Phase:** ✅ COMPLETE

- ✅ PHI audit logging (8 endpoints, HIPAA-ready)
- ✅ Token revocation (logout works, Redis-backed)
- ✅ Frontend error boundaries (no blank screens)
- ✅ Git history cleanup (no secrets committed)
- ✅ Comprehensive documentation (8 files)

**Production-Ready:**
- ✅ Security (auth, encryption, audit trail)
- ✅ Error handling (boundaries, graceful degradation)
- ✅ Testing (24+ passing tests)
- ✅ Deployment (Railway + Vercel configured)

---

**Built with professional patterns from enterprise medical AI systems.**  
*Last updated: 2026-05-08*
