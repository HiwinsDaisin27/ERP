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
- `/sites` lists site IDs for workflows
- `/workers` lists worker IDs for workflows
- `/cancel` cancels the current guided workflow
- `/help` shows available commands

## Telegram Intake Role

Telegram is now the field intake channel. Users send natural text updates, and the backend stores them in `telegram_data_submissions` for the LLM tool-calling insertion phase.

Telegram should be used for:

- Attendance updates
- Material updates
- Site expenses
- Progress updates
- Daily report delivery

Telegram should not be used for payroll, salary edits, payment approvals, or confidential database questions.

Telegram LLM insertion flow:

1. User sends a natural-language field update.
2. Backend stores it in `telegram_data_submissions`.
3. OpenRouter extracts one approved backend tool call.
4. Telegram asks the user to confirm.
5. After confirmation, the backend executes the tool and writes to PostgreSQL.

The manual guided workflow engine remains in code as a fallback/admin utility, but it is no longer exposed in the Telegram menu.

See [docs/architecture-next-phase.md](docs/architecture-next-phase.md) for the next-phase plan.
