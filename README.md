# TheSecond

Site-centric construction ERP for Telegram field intake, management dashboard, payroll workbook, worker/site master data, and AI-assisted reporting.

## Components

| Component | Role |
|---|---|
| FastAPI backend | APIs, auth, payroll, dashboard, assistant, Telegram webhook |
| React/Vite frontend | Management web app |
| Supabase PostgreSQL | Production database |
| Telegram bot | Supervisor field intake |
| OpenRouter | LLM extraction and assistant responses |

## Local Setup

```powershell
cd "C:\Users\HIWINS DAISIN\OneDrive\Desktop\TheSecond"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m app.db.init_db
```

Frontend:

```powershell
cd "C:\Users\HIWINS DAISIN\OneDrive\Desktop\TheSecond\web"
npm install
npm.cmd run dev
```

Backend:

```powershell
cd "C:\Users\HIWINS DAISIN\OneDrive\Desktop\TheSecond"
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
Frontend: http://127.0.0.1:5173
Backend:  http://127.0.0.1:8000
Docs:     http://127.0.0.1:8000/docs
```

## Admin User

Create or reset the admin account:

```powershell
python -m app.db.manage_admin --email you@example.com --password "StrongPasswordHere" --full-name "Admin"
```

## Telegram

Telegram is for approved supervisors to submit attendance, material, expense, and progress updates. New sites and workers are managed only through the secure website.

Local tunnel:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Set `PUBLIC_WEBHOOK_BASE_URL` to the Cloudflare URL, then:

```powershell
python -m app.telegram.set_webhook
python -m app.telegram.get_webhook_info
```

Restrict production Telegram access:

```env
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
```

## Production

The free-tier deployment target is:

| Component | Host |
|---|---|
| Backend | Render free web service |
| Frontend | Vercel Hobby |
| Database | Supabase free plan |

Deployment config files:

```text
render.yaml
Dockerfile
web/vercel.json
```

Full deployment steps and environment variables are in [docs/production-deployment.md](docs/production-deployment.md).

## Maintenance

Preview a database reset:

```powershell
python -m app.db.reset_db --dry-run
```

Clear operational data while preserving website users:

```powershell
python -m app.db.reset_db --production --confirm RESET_THESECOND_DATABASE
```

Clear everything, including website users:

```powershell
python -m app.db.reset_db --production --include-users --confirm RESET_THESECOND_DATABASE
```
