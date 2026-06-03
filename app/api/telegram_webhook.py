from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.telegram_update_handler import TelegramUpdateHandler


router = APIRouter(prefix="/webhooks", tags=["telegram"])


async def handle_telegram_update(
    request: Request,
    db: Session,
    telegram_secret_token: str | None,
) -> dict[str, bool]:
    if settings.telegram_webhook_secret and telegram_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram webhook secret")

    payload = await request.json()
    handler = TelegramUpdateHandler(db)
    await handler.handle_update(payload)
    return {"ok": True}


@router.post("")
async def telegram_webhook_legacy_path(
    request: Request,
    db: Session = Depends(get_db),
    telegram_secret_token: str | None = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict[str, bool]:
    return await handle_telegram_update(request, db, telegram_secret_token)


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    telegram_secret_token: str | None = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict[str, bool]:
    return await handle_telegram_update(request, db, telegram_secret_token)
