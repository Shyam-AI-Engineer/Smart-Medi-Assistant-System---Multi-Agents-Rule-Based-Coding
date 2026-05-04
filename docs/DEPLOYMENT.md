# Deployment Guide: Railway + Vercel

This guide covers deploying the Smart Medi Assistant to production using Railway for the backend and Vercel for the frontend.

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│  Vercel (Frontend)                          │
│  https://<your-app>.vercel.app              │
│  ├─ Next.js 14 (standalone output)          │
│  └─ Uses NEXT_PUBLIC_API_URL for API calls  │
└────────────────────┬────────────────────────┘
                     │
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────┐
│  Railway (Backend)                          │
│  https://<your-app>.up.railway.app          │
│  ├─ FastAPI (uvicorn, 2 workers)            │
│  ├─ PostgreSQL 16 (managed service)         │
│  └─ Redis 7 (managed service)               │
└─────────────────────────────────────────────┘
```

---

## Prerequisites

- **GitHub account** with this repository pushed
- **Railway.app account** (free tier available)
- **Vercel account** (free tier available)
- **Git CLI** installed locally

---

## Step 1: Prepare the Repository

### 1.1 Ensure `.env.example` is committed (no secrets)

```bash
# Check that .env (with actual secrets) is in .gitignore
cat .gitignore | grep "^\.env$"
# Should output: .env

# .env.example should be committed
git add .env.example
git commit -m "chore: ensure .env.example is committed"
```

### 1.2 Verify GitHub Actions workflow exists

```bash
# CI should run on push
ls -la .github/workflows/ci.yml
# Should exist and contain GitHub Actions config
```

### 1.3 Push to GitHub main branch

```bash
git push origin main
```

Verify that CI workflow runs and passes:
1. Go to https://github.com/your-org/smart-medi-assistant/actions
2. Click on the latest commit
3. Verify both "Backend Tests" and "Frontend Lint & Type Check" pass ✅

---

## Step 2: Deploy Backend to Railway

### 2.1 Create Railway Project

1. Go to https://railway.app
2. Click **New Project**
3. Click **Deploy from GitHub repo**
4. Search for `smart-medi-assistant` and connect it
5. Click **Deploy**

### 2.2 Add PostgreSQL Plugin

1. In Railway dashboard, click **+ Add**
2. Select **Database** → **PostgreSQL**
3. A new PostgreSQL service appears with auto-generated `DATABASE_URL`
4. Note the connection string (you'll see it in logs)

### 2.3 Add Redis Plugin

1. Click **+ Add** again
2. Select **Database** → **Redis**
3. A new Redis service appears with auto-generated `REDIS_URL`

### 2.4 Configure Environment Variables

In the Railway backend service, go to **Variables** tab and add:

#### Copied from Railway plugins (auto-filled):
```
DATABASE_URL=postgresql://...  # Auto from PostgreSQL plugin
REDIS_URL=redis://...           # Auto from Redis plugin
```

#### Set manually:
```
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=<generate random 64-char string>
CORS_ORIGINS=https://<your-app>.vercel.app
EURI_API_KEY=<your Euri API key>
EURI_BASE_URL=https://api.euron.one/api/v1/euri
EURI_EMBEDDING_MODEL=gemini-embedding-2-preview
EURI_LLM_MODEL=gpt-4o-mini
FAISS_INDEX_PATH=/app/data/faiss_index
EMBEDDING_DIMENSIONS=768
RAG_TOP_K=5
TEMPERATURE_RAG=0.3
APP_NAME=Smart Medi Assistant
```

#### Generate JWT_SECRET_KEY (run locally):
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Copy the output into JWT_SECRET_KEY variable
```

### 2.5 Verify Backend Deployment

1. Railway auto-deploys from `main` branch (via webhook)
2. Go to **Deployments** tab and wait for a new deployment to start
3. Once deployed, click the service to see the **Public URL** (e.g., `https://app-prod.up.railway.app`)
4. Test the health check:
   ```bash
   curl https://<your-app>.up.railway.app/health
   # Should return: {"status": "ok", "version": "0.1.0"}
   ```

**If deployment fails:**
- Click the failed deployment to view logs
- Common issues:
  - `DATABASE_URL` missing or malformed → Re-copy from PostgreSQL plugin
  - `EURI_API_KEY` invalid → Check key is correct
  - Port mismatch → Railway automatically uses `$PORT` env var (already configured in `railway.toml`)

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Project

1. Go to https://vercel.com/new
2. Click **Import Git Repository**
3. Search for `smart-medi-assistant` and click **Import**
4. Under **Root Directory**, select `./frontend`
5. Click **Deploy**

### 3.2 Configure Environment Variables

After deployment, go to **Settings** → **Environment Variables** and add:

```
NEXT_PUBLIC_API_URL=https://<your-app>.up.railway.app
```

Replace `<your-app>` with your actual Railway app name.

### 3.3 Redeploy to Apply Environment Variables

1. Go to **Deployments** tab
2. Click the three dots on the latest deployment
3. Click **Redeploy**
4. Wait for deployment to complete

### 3.4 Verify Frontend Deployment

1. Go to **Domains** tab to see your Vercel URL (e.g., `https://app-prod.vercel.app`)
2. Visit the URL in a browser
3. You should see the Smart Medi login page
4. Open browser DevTools (F12) → **Network** tab
5. Try to login — you should see API calls going to `https://<your-app>.up.railway.app/api/v1/auth/login`

**If API calls fail (CORS error or 404):**
- Check that `NEXT_PUBLIC_API_URL` is correctly set in Vercel
- Check that `CORS_ORIGINS` in Railway includes the Vercel URL
- Redeploy both if you changed either

---

## Step 4: Post-Deployment Setup

### 4.1 Database Migrations

The backend automatically initializes the database schema on startup via `init_db()` in `backend/app/extensions.py`.

**If you need to run manual migrations later** (only for schema changes after deployment):
```bash
# This is for local development only
# Production migrations should be via alembic eventually
cd backend
alembic upgrade head
```

### 4.2 Seed Initial Data (Optional)

To add sample data for testing:

```bash
# Create a script: backend/scripts/seed_db.py
python backend/scripts/seed_db.py --db-url="<production-database-url>"
```

This is optional — the app works with an empty database.

### 4.3 Monitor Logs

**Railway backend logs:**
- Go to Railway dashboard → select backend service → **Logs** tab
- Watch for any errors after deployment

**Vercel frontend logs:**
- Go to Vercel dashboard → Deployments → click a deployment
- Click **Runtime Logs** tab to see any build or runtime errors

---

## Verification Checklist

- [ ] Railway backend deployed and healthy
  - [ ] `GET /health` returns 200
  - [ ] `GET /` returns API info
  - [ ] PostgreSQL plugin created with `DATABASE_URL`
  - [ ] Redis plugin created with `REDIS_URL`
  - [ ] All env vars set in Railway dashboard

- [ ] Vercel frontend deployed
  - [ ] Deployed to `https://<your-app>.vercel.app`
  - [ ] `NEXT_PUBLIC_API_URL` set to Railway URL
  - [ ] Frontend loads (you see the UI)

- [ ] End-to-end test
  - [ ] Navigate to frontend URL in browser
  - [ ] Login with test credentials
  - [ ] See dashboard load with data from backend
  - [ ] Open DevTools Network tab — all API calls succeed (no 401/403/500 errors)

---

## Troubleshooting

### Backend Health Check Fails (Railway)

```bash
curl -v https://<your-app>.up.railway.app/health
# If this returns 502 or timeout:
```

**Checklist:**
1. Is PostgreSQL plugin running? (Check Railway dashboard)
2. Is Redis plugin running? (Check Railway dashboard)
3. Check `DATABASE_URL` format in Railway variables (from PostgreSQL plugin)
4. Check Rails logs for startup errors

### Frontend Shows "API is Unreachable" or CORS Error

**Check:**
1. `NEXT_PUBLIC_API_URL` in Vercel environment variables is correct
2. `CORS_ORIGINS` in Railway includes the Vercel URL (https://<your-app>.vercel.app)
3. Redeploy Vercel after changing env vars
4. Check browser console (F12) for exact error message

### CI/CD Not Running

1. Ensure `main` branch protection rules allow automatic deploys
2. Check `.github/workflows/ci.yml` is in repository
3. In GitHub settings, go to **Actions** → check it's enabled
4. Push a test commit: `git commit --allow-empty -m "test: trigger CI"`

### Can't Log In (401 Unauthorized)

**Check:**
1. JWT_SECRET_KEY is set in Railway env vars
2. User credentials are correct (registered via `/api/v1/auth/register`)
3. Check backend logs for auth errors

### Database Connection Errors

```bash
# Test DB connection from local machine
psql postgresql://user:pass@host:port/dbname -c "SELECT 1"
# Should return: (1 row)
```

If connection fails:
1. Check DATABASE_URL is copied exactly from Railway
2. Check PostgreSQL plugin is running
3. Check IP whitelisting (Railway includes all IPs by default)

---

## Ongoing Operations

### Monitoring

1. **Check health daily:**
   ```bash
   curl https://<your-app>.up.railway.app/health
   ```

2. **Monitor logs in Railway:**
   - Backend service → Logs tab
   - Watch for errors, rate limits, database issues

3. **Monitor Vercel build status:**
   - Deployments tab → click latest deployment
   - Check build logs and runtime logs

### Updating Code

1. Make changes locally and commit
2. Push to `main` branch
3. GitHub Actions CI runs automatically (tests on backend, lint on frontend)
4. If CI passes, Railway and Vercel auto-deploy the new version
5. Takes ~2-3 minutes for both to be live

### Rollback

If a deployment breaks production:

**Railway:**
1. Go to **Deployments** tab
2. Find the last working deployment
3. Click → **Redeploy**

**Vercel:**
1. Go to **Deployments** tab
2. Click the last working deployment → **Promote to Production**

---

## Next Steps

1. ✅ Backend deployed to Railway
2. ✅ Frontend deployed to Vercel
3. ✅ CI/CD pipeline running
4. ➜ Monitor logs for first week
5. ➜ Set up email alerts (optional)
6. ➜ Set up uptime monitoring (Pingdom, Statuspage)
7. ➜ Enable database backups (Railway dashboard → PostgreSQL → Backups)

---

## Support

For issues:
- **Railway docs:** https://docs.railway.app
- **Vercel docs:** https://vercel.com/docs
- **Smart Medi repo:** Check GitHub Issues or README.md

Happy deploying! 🚀
