# TheSecond Backend

Database-centered FastAPI backend for the construction ERP Telegram automation system.

This first stage intentionally has no LLM integration. Telegram sends updates to the backend, the backend stores users/messages/workflow state in PostgreSQL, and business logic will be added as deterministic API/services.

## Setup

1. Create a local `.env` file from `.env.example`.
2. Fill in:

```env
DATABASE_URL=postgresql://postgres:<password>@db.kqyjmfqtduboiqcbypyu.supabase.co:5432/postgres
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_ADMIN_CHAT_ID=1850995106
TELEGRAM_WEBHOOK_SECRET=<random-secret>
PUBLIC_WEBHOOK_BASE_URL=<https-url-after-deploy-or-tunnel>
```

Do not commit `.env`.

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```txt
http://127.0.0.1:8000/health
```

## Initialize Database

```bash
python -m app.db.init_db
```

## Telegram Webhook

After the backend has a public HTTPS URL:

```bash
python -m app.telegram.set_webhook
```

The webhook endpoint is:

```txt
POST /webhooks/telegram
```

## Current Bot Commands

- `/start` opens the main menu
- `/hr` opens HR operations
- `/site` opens site/procurement operations
- `/report` opens reports
- `/help` shows available commands

