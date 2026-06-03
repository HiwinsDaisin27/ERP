from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(tags=["root"])


@router.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "status": "running",
        "stage": "telegram-backend-no-llm",
        "protocols": {
            "health": "GET /health",
            "telegram_webhook": "POST /webhooks/telegram",
            "telegram_webhook_compat": "POST /webhooks",
            "api_docs": "GET /docs",
        },
        "telegram": {
            "webhook_ready": True,
            "requires_public_https_url": True,
            "llm_enabled": False,
        },
    }
