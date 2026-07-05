from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(tags=["root"])


@router.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "running",
        "stage": "telegram-intake-dashboard-payroll-apis",
        "protocols": {
            "health": "GET /health",
            "api_docs": "GET /docs",
            "auth_login": "POST /auth/login",
            "auth_bootstrap": "POST /auth/bootstrap",
            "dashboard_overview": "GET /dashboard/overview",
            "assistant_chat": "POST /assistant/chat",
            "payroll_workbook": "GET /payroll/periods/{period_id}/workbook",
            "telegram_webhook": "POST /webhooks/telegram",
        },
        "telegram": {
            "webhook_ready": True,
            "requires_public_https_url": True,
            "llm_enabled": settings.llm_insertion_ready,
            "llm_provider": settings.llm_insertion_provider or "openrouter",
            "llm_model": settings.llm_insertion_model,
        },
        "website_auth": {
            "jwt_configured": bool(settings.jwt_secret),
        },
    }
