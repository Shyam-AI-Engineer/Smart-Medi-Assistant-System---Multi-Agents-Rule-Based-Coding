# Developer Security Guide

## Quick Start

### 1. Clone & Setup

```bash
git clone <repo>
cd smart-medi-assistant

# Install pre-commit hook (prevents accidental secret commits)
# Hook is already in .git/hooks/pre-commit

# Create local environment files (git-ignored)
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Edit with your local values
# - Backend: Add JWT_SECRET_KEY, EURI_API_KEY, database URL
# - Frontend: Add NEXT_PUBLIC_API_URL (http://localhost:8000/api for local dev)

# Install dependencies
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# Start services
docker-compose up -d  # PostgreSQL + Redis
python backend/main.py  # Backend
npm run dev --prefix frontend  # Frontend
```

### 2. Pre-Commit Hook (Already Installed)

The pre-commit hook automatically runs before each commit. It prevents:

- ✅ Committing `.env` files
- ✅ Committing `.env.local` files  
- ✅ Committing API keys or secrets
- ✅ Committing database passwords

**If the hook blocks your commit:**
```bash
# 1. Remove secret files from staging
git reset HEAD .env
git reset HEAD .env.local

# 2. Verify they're in .gitignore
# 3. Try committing again
git commit -m "your message"

# Emergency override (NOT recommended)
# Only use if you KNOW the commit is safe
git commit --no-verify -m "your message"
```

---

## Environment Variables

### Required for Local Development

**Backend (`backend/.env`):**
```bash
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=<your-generated-32-char-hex>

# Optional: Your Euri API key if testing AI features
EURI_API_KEY=sk-proj-xxxxx

# These use defaults (local docker services)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smart_medi_dev
REDIS_URL=redis://localhost:6379/0
```

**Frontend (`frontend/.env.local`):**
```bash
# Points to local backend
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Do NOT Commit
- `backend/.env` — Local secrets
- `frontend/.env.local` — Local config
- Any file with actual API keys, tokens, passwords

### Safe to Commit
- `backend/.env.example` — Template with placeholder values
- `frontend/.env.local.example` — Template
- `frontend/.env.production` — Only public vars (NEXT_PUBLIC_ prefix)

---

## Secret Types & Handling

| Secret | Purpose | Where? | Rotation |
|--------|---------|--------|----------|
| `JWT_SECRET_KEY` | Sign access tokens | Backend .env | Yearly |
| `EURI_API_KEY` | AI service auth | Backend .env | On compromise |
| `DATABASE_URL` | PostgreSQL connection | Backend .env (prod: Railway) | 6 months |
| `REDIS_URL` | Cache connection | Backend .env (prod: Railway) | 6 months |
| `OPENAI_API_KEY` | OpenAI API (legacy) | Backend .env | Yearly |

---

## Git Security Best Practices

### Before Committing

```bash
# 1. Check what you're committing
git diff --cached

# 2. Verify no .env files
git diff --cached --name-only | grep "\.env"
# (Should return nothing)

# 3. Verify no secret patterns
git diff --cached | grep -iE "api_key|secret|password|Bearer"
# (Should return nothing)

# 4. Commit
git commit -m "your message"
# Pre-commit hook will block if it detects secrets
```

### If You Accidentally Commit a Secret

**Immediately:**
```bash
# 1. Rotate the compromised secret
# - Generate new JWT_SECRET_KEY
# - Generate new API keys
# - Update .env locally and in deployment platform

# 2. Remove from git history
git reset --soft HEAD~1  # Undo last commit
git reset HEAD <file>   # Unstage the file
git commit -m "Remove secret file"
git push

# 3. For older commits, use filter-branch or filter-repo
# (Advanced — ask team lead)
```

**Tell the team** — Secrets that made it to git are compromised regardless of rotation.

---

## Code Review Checklist

When reviewing PRs, verify:

- [ ] No `.env` files in diff
- [ ] No hardcoded API keys, passwords, tokens
- [ ] All secrets use `os.getenv()` with safe defaults
- [ ] Defaults only use localhost/dummy credentials (not production)
- [ ] Example files have no real values
- [ ] `.gitignore` includes `.env*` patterns

---

## Local Development Troubleshooting

### "TypeError: unsupported operand type(s)"

**Cause:** Missing JWT_SECRET_KEY in backend/.env  
**Fix:**
```bash
# Generate and add to backend/.env
python -c "import secrets; print(secrets.token_hex(32))"
# Copy output as JWT_SECRET_KEY=...
```

### "Connection refused: backend not running"

**Cause:** Frontend trying to reach backend at wrong URL  
**Fix:**
```bash
# In frontend/.env.local:
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Make sure backend is running:
cd backend && python -m uvicorn app.main:app --reload
```

### "No module named 'app.models'"

**Cause:** Dependencies not installed  
**Fix:**
```bash
cd backend
pip install -r requirements.txt
```

---

## Deployment Security

### Before Deploying to Production

**Railway (Backend):**
1. Set `ENVIRONMENT=production` in Railway environment
2. Generate new `JWT_SECRET_KEY` (not dev one)
3. Add `EURI_API_KEY` from production Euri account
4. DATABASE_URL and REDIS_URL auto-provided by Railway
5. Verify no `.env` files in git

**Vercel (Frontend):**
1. Set `NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api`
2. Verify no secrets in environment variables
3. Only NEXT_PUBLIC_ variables can be in frontend

### Secrets Rotation Schedule

- **Monthly**: Check for exposed secrets in logs
- **Quarterly**: Rotate EURI_API_KEY
- **Yearly**: Rotate JWT_SECRET_KEY, Database password
- **On compromise**: Rotate immediately and investigate

---

## Monitoring & Alerts

### What to Watch For

1. **Git commits** — Pre-commit hook blocks secrets ✅
2. **Application logs** — Monitor for failed auth, API errors
3. **Database logs** — Monitor for unusual access patterns
4. **API usage** — Alert on unusual token/API key usage

### Incident Response

**If you suspect a secret leaked:**

1. **Immediately rotate** the secret
2. **Update deployment** with new value
3. **Monitor for abuse** — Check logs for unauthorized access
4. **Review git history** — Search for when/how it was exposed
5. **Notify team** — Update security docs

---

## Resources

- `ENVIRONMENT_VARIABLES.md` — Full env var reference
- `backend/.env.example` — Backend template
- `frontend/.env.local.example` — Frontend template  
- `.git/hooks/pre-commit` — Secret detection hook
- `CLAUDE.md` — Project architecture

---

## Questions?

When in doubt:
1. Check if it belongs in `.env` → Don't commit it
2. Check if it's a secret → Use `os.getenv()`
3. Check `.gitignore` → Is it there?
4. Run pre-commit hook → Does it pass?
5. Ask the team → Never guess with security

**Golden Rule:** If you wouldn't want it on the internet, don't commit it to git.
