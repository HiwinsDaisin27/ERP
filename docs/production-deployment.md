# Production Deployment Guide

This project has four moving parts. Deploy them in this order.

| Component | Role | Recommended host |
|---|---|---|
| PostgreSQL | Database | Supabase (already in use) |
| Backend API | FastAPI + Telegram webhook + LLM | Railway, Render, or Fly.io |
| Frontend | React dashboard | Vercel or Netlify |
| Telegram | Field intake | Points webhook to backend URL |

---

## Phase 0 — Pre-flight checklist

Before deploying, confirm locally:

```powershell
# Backend
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd web
npm install
npm run build

# Telegram (with cloudflared or after deploy)
python -m app.telegram.set_webhook
```

Verify:

- [ ] Login works on the website
- [ ] Dashboard loads data
- [ ] Payroll workbook opens
- [ ] Intelligence Assistant answers and exports XLSX
- [ ] Telegram message → LLM extract → confirm → DB write

---

## Phase 1 — Production environment variables

Set these on your **backend host** (never commit real values):

```env
# Core
DATABASE_URL=postgresql://...
ENVIRONMENT=production
APP_BASE_URL=https://api.yourdomain.com
FRONTEND_ORIGINS=https://your-vercel-app.vercel.app
JWT_SECRET=<long-random-string-min-32-chars>

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=<random-secret>
PUBLIC_WEBHOOK_BASE_URL=https://api.yourdomain.com

# LLM — insertion (Telegram)
LLM_INSERTION_PROVIDER=openrouter
LLM_INSERTION_API_KEY=
LLM_INSERTION_MODEL=openrouter/free
LLM_INSERTION_FALLBACK_MODELS=google/gemini-2.5-flash-lite

# LLM — retrieval (website assistant)
LLM_RETRIEVAL_PROVIDER=openrouter
LLM_RETRIEVAL_API_KEY=
LLM_RETRIEVAL_MODEL=google/gemini-2.5-flash
LLM_RETRIEVAL_FALLBACK_MODELS=google/gemini-2.5-pro

# Reports
REPORT_EXPORT_DIR=data/exports
```

Set on your **frontend host**:

```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

For the current free-tier launch:

- Backend host: Render web service from `render.yaml`
- Frontend host: Vercel project with root directory `web`
- Database: Supabase session pooler URL
- `APP_BASE_URL` and `PUBLIC_WEBHOOK_BASE_URL` should both be the final Render backend URL.
- `FRONTEND_ORIGINS` should be the final Vercel frontend URL.

Generate secrets:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Create production admin (run once against production DB from your machine or host shell):

```powershell
python -m app.db.manage_admin --email you@company.com --password <strong-password> --full-name Admin
```

---

## Phase 2 — Deploy backend API

### Option A: Railway (recommended for simplicity)

1. Push repo to GitHub.
2. Create a Railway project → Deploy from GitHub.
3. Set root directory to repo root.
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all backend env vars from Phase 1.
6. Add a persistent volume mounted at `/app/data/exports` for report files (or use cloud storage later).
7. Railway gives you a URL like `https://your-app.up.railway.app` — use this as `PUBLIC_WEBHOOK_BASE_URL` and `APP_BASE_URL`.

### Option B: Docker

```powershell
docker build -t thesecond-api .
docker run -p 8000:8000 --env-file .env -v thesecond-exports:/app/data/exports thesecond-api
```

### Option C: Render Blueprint

1. Push this repo to GitHub.
2. Render → **New** → **Blueprint**.
3. Select the GitHub repo.
4. Render reads `render.yaml` and creates `thesecond-api`.
5. Fill every `sync: false` environment variable in Render.
6. Deploy.

Required Render env vars:

```env
DATABASE_URL=<Supabase session pooler URL>
TELEGRAM_BOT_TOKEN=<BotFather token>
TELEGRAM_ADMIN_CHAT_ID=<your admin chat id>
TELEGRAM_WEBHOOK_SECRET=<same local/prod secret>
TELEGRAM_ALLOWED_USER_IDS=<comma-separated supervisor Telegram user ids>
PUBLIC_WEBHOOK_BASE_URL=https://thesecond-api.onrender.com
JWT_SECRET=<long random secret>
APP_BASE_URL=https://thesecond-api.onrender.com
FRONTEND_ORIGINS=https://your-vercel-app.vercel.app
LLM_INSERTION_API_KEY=<OpenRouter key>
LLM_RETRIEVAL_API_KEY=<OpenRouter key or blank if insertion key should be reused>
GROQ_API_KEY=
```

### After backend is live

```powershell
# From your machine, with production .env or Railway shell
python -m app.db.init_db
python -m app.db.manage_admin --email you@company.com --password <password> --full-name Admin
python -m app.telegram.set_webhook
python -m app.telegram.get_webhook_info
```

Health check: `GET https://api.yourdomain.com/health` → `{"status":"ok"}`

---

## Phase 3 — Deploy frontend

### Vercel

1. Import GitHub repo.
2. Set **Root Directory** to `web`.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Environment variable: `VITE_API_BASE_URL=https://your-render-backend.onrender.com`
6. Deploy.

### Update backend CORS

Add your frontend URL to `app/main.py` CORS `allow_origins`, e.g.:

```python
"https://your-app.vercel.app",
"https://dashboard.yourdomain.com",
```

Redeploy backend after this change.

---

## Phase 4 — Telegram permanent webhook

Once backend has a **stable HTTPS URL** (not cloudflared):

1. Set `PUBLIC_WEBHOOK_BASE_URL=https://api.yourdomain.com` in production env.
2. Run `python -m app.telegram.set_webhook`.
3. Confirm with `python -m app.telegram.get_webhook_info`.

You no longer need cloudflared in production.

---

## Phase 5 — Post-deploy verification

| Test | Expected |
|---|---|
| `GET /health` | 200 OK |
| Website login | Dashboard loads |
| Intelligence Assistant | Answers + XLSX download |
| Telegram plain-text update | Confirm/reject buttons |
| Payroll finalize | Period locks |

---

## Production database reset

Use the guarded reset CLI from your local machine when `.env` points at the target Supabase database.
The deployed Render/Vercel app reads the same database, so the UI reflects the cleared data on the next refresh or dashboard polling cycle.

Preview what would be cleared:

```powershell
python -m app.db.reset_db --dry-run
```

Clear operational data while preserving website login users/admins:

```powershell
python -m app.db.reset_db --production --confirm RESET_THESECOND_DATABASE
```

Clear everything, including website users/admins:

```powershell
python -m app.db.reset_db --production --include-users --confirm RESET_THESECOND_DATABASE
```

After `--include-users`, recreate an admin before trying to sign in:

```powershell
python -m app.db.manage_admin --email you@company.com --password <strong-password> --full-name Admin
```

Avoid exposing this as a normal UI button. A future maintenance screen can be added, but it should require ADMIN role, re-entered password, a typed confirmation phrase, and ideally a server-side environment flag.

---

## Google Sheets workflow

The assistant exports **XLSX** (and CSV). To use Google Sheets:

1. Download the XLSX from the assistant.
2. Google Drive → Upload → Open with Google Sheets, **or**
3. Google Sheets → File → Import → Upload.

Direct auto-push to Google Sheets requires Google Cloud service account setup (optional future enhancement).

---

## Custom domain (optional)

1. Point `api.yourdomain.com` → backend host.
2. Point `app.yourdomain.com` → Vercel frontend.
3. Update `APP_BASE_URL`, `PUBLIC_WEBHOOK_BASE_URL`, `VITE_API_BASE_URL`, CORS origins.
4. Re-run Telegram `set_webhook`.

---

## Common production errors

| Symptom | Fix |
|---|---|
| Telegram webhook 401 | `TELEGRAM_WEBHOOK_SECRET` must match what Telegram sends |
| LLM_FAILED on Telegram | Check OpenRouter key; use `openrouter/free` model |
| Assistant empty response | Set `LLM_RETRIEVAL_API_KEY` or reuse insertion key |
| CORS error in browser | Add frontend URL to backend CORS list |
| Login works locally, not prod | `JWT_SECRET` must be set in production |
| Report download 404 | Ensure `data/exports` volume persists on host |

---

## Security reminders

- Rotate any API key ever pasted into chat or committed.
- Use strong admin password; remove bootstrap endpoint exposure if desired.
- Keep payroll and assistant behind `ADMIN` / `MANAGEMENT` roles only.
- Supabase: enable SSL, restrict DB access to backend IP if possible.
