# Environment Variables & Secrets Management

## Status ✅

**Git History:** CLEAN  
**Current Tracked Files:**
- ✅ `backend/.env.example` — Template (safe)
- ✅ `frontend/.env.local.example` — Template (safe)  
- ✅ `frontend/.env.production` — Only contains `NEXT_PUBLIC_API_URL` (safe)

**Never Committed:**
- `.env` (root)
- `backend/.env`
- `frontend/.env.local`
- Any actual configuration files

**Local .env Files:**
- `frontend/.env.local` exists locally, properly `.gitignore`'d
- Contains only Vercel OIDC token (temporary, scoped, expired)

---

## Environment Variables Structure

### Backend (`backend/.env`)

```bash
# ==============================================================================
# CORE CONFIGURATION
# ==============================================================================
ENVIRONMENT=development|staging|production
DEBUG=False

# ==============================================================================
# SECURITY (CRITICAL - Never commit!)
# ==============================================================================
JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==============================================================================
# DATABASE (CRITICAL - Never commit!)
# ==============================================================================
DATABASE_URL=postgresql://user:password@host:5432/database_name

# Production: Railway provides via secret environment
# Development: Use docker-compose database

# ==============================================================================
# CACHE
# ==============================================================================
REDIS_URL=redis://localhost:6379/0
# Production: Railway provides via secret environment

# ==============================================================================
# AI / EXTERNAL SERVICES (CRITICAL - Never commit!)
# ==============================================================================
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx  # Legacy (if still used)
EURI_API_KEY=sk-proj-xxxxxxxxxxxxx    # Euri API key
EURI_BASE_URL=https://api.euron.one/api/v1/euri
EURI_EMBEDDING_MODEL=gemini-embedding-2-preview
EURI_LLM_MODEL=gpt-4o-mini

# ==============================================================================
# VECTOR DATABASE (FAISS)
# ==============================================================================
FAISS_INDEX_PATH=./data/faiss_index
EMBEDDING_DIMENSIONS=768
CHUNK_SIZE=1024
CHUNK_OVERLAP=256
RAG_TOP_K=5
TEMPERATURE_RAG=0.3

# ==============================================================================
# CORS & DEPLOYMENT
# ==============================================================================
FRONTEND_URL=http://localhost:3000
# Production: https://yourdomain.com
```

### Frontend (`frontend/.env.local`)

```bash
# Development only — Never commit!
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Production is handled by frontend/.env.production (safe to commit)
```

### Frontend Production (`frontend/.env.production`)

```bash
# Safe to commit — Only public environment variables (NEXT_PUBLIC_ prefix)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api
```

---

## Setup Instructions

### Development

#### 1. Backend

```bash
cd backend

# Create .env from example
cp .env.example .env  # (or create manually)

# Edit .env with your values:
# - Generate JWT_SECRET_KEY
# - Set DATABASE_URL to local postgres
# - Set REDIS_URL to local redis
# - Set EURI_API_KEY if using AI features

# Install and run
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

#### 2. Frontend

```bash
cd frontend

# Create .env.local (git-ignored)
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000/api
EOF

# Install and run
npm install
npm run dev
```

### Production (Railway/Vercel)

#### Backend (Railway)

Set environment variables in Railway dashboard:
- `ENVIRONMENT=production`
- `JWT_SECRET_KEY=<strong-random-value>`
- `DATABASE_URL=<auto-provided by Railway postgres plugin>`
- `REDIS_URL=<auto-provided by Railway redis plugin>`
- `EURI_API_KEY=<your-api-key>`
- All other config vars

#### Frontend (Vercel)

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api`

---

## Security Checklist

### Before Committing Code

- [ ] No `.env` file in git (should be in `.gitignore`)
- [ ] No `.env.local` file in git (should be in `.gitignore`)
- [ ] No hardcoded API keys, tokens, or passwords
- [ ] No database connection strings in code
- [ ] All secrets use `os.getenv()` with defaults for dev only
- [ ] Defaults are for LOCAL development (postgres:postgres@localhost, etc.)
- [ ] `.gitignore` includes all `.env*` patterns
- [ ] Example files (`.env.example`) have no real secrets

### Before Deploying to Production

- [ ] All `os.getenv()` calls have appropriate keys in deployment environment
- [ ] Database uses production credentials from secrets manager (Railway/Vercel)
- [ ] API keys are strong and environment-specific
- [ ] JWT_SECRET_KEY is different from development
- [ ] CORS origins set to production domain only
- [ ] No debug/verbose logging in production
- [ ] Database backups enabled
- [ ] Environment is set to `production`

---

## Common Issues & Solutions

### Issue: "KeyError: JWT_SECRET_KEY"

**Cause:** `.env` not created or `JWT_SECRET_KEY` not set  
**Fix:**
```bash
cd backend
python -c "import secrets; print(secrets.token_hex(32))"
# Copy output and add to .env: JWT_SECRET_KEY=<output>
```

### Issue: "Cannot connect to database"

**Cause:** DATABASE_URL not set or database not running  
**Fix:**
```bash
# Start database
docker-compose up -d

# Check DATABASE_URL in .env points to it
# Default: postgresql://postgres:postgres@localhost:5432/smart_medi_dev
```

### Issue: "EURI_API_KEY not set"

**Cause:** Missing in `.env` or wrong key  
**Fix:**
- Get API key from Euri dashboard
- Add to `.env`: `EURI_API_KEY=sk-proj-xxxxx`

### Issue: "frontend/.env.local committed to git"

**Cause:** File was added before `.gitignore` rule
**Fix:**
```bash
# Remove from git but keep local file
git rm --cached frontend/.env.local
git commit -m "Remove .env.local from git (still local)"
```

---

## Secrets Rotation

### How Often

- **API Keys**: Yearly or on compromise
- **JWT_SECRET_KEY**: Yearly (requires token refresh)
- **Database Password**: Every 6 months
- **Refresh tokens**: Automatic revocation on logout

### Process

1. Generate new value
2. Add as new secret in deployment platform
3. Update code to use new key (or toggle via config)
4. Wait for old tokens to expire (TTL-based cleanup)
5. Remove old key from secrets manager

---

## Git History

Last audit: 2026-05-08

**Findings:**
- ✅ No .env files ever committed
- ✅ No API keys in git history
- ✅ All secrets properly excluded by .gitignore
- ✅ Safe example files tracked
- ✅ Frontend .env.production safe (public vars only)

**Protected:**
- `backend/.env` — Never committed ✅
- `frontend/.env.local` — Never committed ✅
- `frontend/.env.*.local` — Never committed ✅
- API keys and secrets — Never committed ✅

---

## Next Steps

1. **Environment Parity** — Dev/staging/prod use identical secrets structure
2. **Secrets Scanning** — Pre-commit hook to detect accidental secret commits
3. **Audit Trail** — Log who accessed/rotated each secret
4. **Infrastructure** — Migrate to BAA-eligible providers for HIPAA compliance
