from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.telegram import TelegramMessage, TelegramUser
from app.services.telegram_client import TelegramClient
from app.services.telegram_keyboards import (
    hr_menu_keyboard,
    main_menu_keyboard,
    reports_menu_keyboard,
    site_menu_keyboard,
)


class TelegramUpdateHandler:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.telegram = TelegramClient()

    async def handle_update(self, payload: dict) -> None:
        update_id = payload.get("update_id")

        if "message" in payload:
            await self._handle_message(update_id, payload["message"], payload)
            return

        if "callback_query" in payload:
            await self._handle_callback(update_id, payload["callback_query"], payload)

    async def _handle_message(self, update_id: int, message: dict, payload: dict) -> None:
        chat = message.get("chat", {})
        from_user = message.get("from", {})
        chat_id = chat["id"]
        text = message.get("text", "")

        self._upsert_user(from_user, chat_id)
        self._log_message(update_id, chat_id, from_user.get("id"), "text", text, payload)
        self.db.commit()

        command = text.strip().split()[0].lower() if text else ""

        if command in {"/start", "start"}:
            await self.telegram.send_message(chat_id, "Choose an operation:", main_menu_keyboard())
        elif command == "/hr":
            await self.telegram.send_message(chat_id, "HR Operations:", hr_menu_keyboard())
        elif command == "/site":
            await self.telegram.send_message(chat_id, "Site & Procurement:", site_menu_keyboard())
        elif command == "/report":
            await self.telegram.send_message(chat_id, "Reports:", reports_menu_keyboard())
        elif command == "/help":
            await self.telegram.send_message(chat_id, self._help_text())
        else:
            await self.telegram.send_message(
                chat_id,
                "I received your message. Use /start to open the operation menu.",
                main_menu_keyboard(),
            )

    async def _handle_callback(self, update_id: int, callback_query: dict, payload: dict) -> None:
        from_user = callback_query.get("from", {})
        message = callback_query.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        data = callback_query.get("data", "")

        if chat_id is None:
            return

        self._upsert_user(from_user, chat_id)
        self._log_message(update_id, chat_id, from_user.get("id"), "callback_query", data, payload)
        self.db.commit()

        if data == "menu:main":
            await self.telegram.send_message(chat_id, "Choose an operation:", main_menu_keyboard())
        elif data == "menu:hr":
            await self.telegram.send_message(chat_id, "HR Operations:", hr_menu_keyboard())
        elif data == "menu:site":
            await self.telegram.send_message(chat_id, "Site & Procurement:", site_menu_keyboard())
        elif data == "menu:reports":
            await self.telegram.send_message(chat_id, "Reports:", reports_menu_keyboard())
        elif data == "menu:help":
            await self.telegram.send_message(chat_id, self._help_text())
        elif data.startswith("hr:") or data.startswith("site:") or data.startswith("report:"):
            await self.telegram.send_message(
                chat_id,
                "This workflow is reserved and ready for the next build step. The backend is already logging this action in the database.",
                main_menu_keyboard(),
            )

    def _upsert_user(self, from_user: dict, chat_id: int) -> None:
        telegram_user_id = from_user.get("id")
        if telegram_user_id is None:
            return

        user = self.db.scalar(
            select(TelegramUser).where(TelegramUser.telegram_user_id == telegram_user_id)
        )

        if user is None:
            user = TelegramUser(telegram_user_id=telegram_user_id, chat_id=chat_id)
            self.db.add(user)

        user.chat_id = chat_id
        user.username = from_user.get("username")
        user.first_name = from_user.get("first_name")
        user.last_name = from_user.get("last_name")

    def _log_message(
        self,
        update_id: int,
        chat_id: int,
        telegram_user_id: int | None,
        message_type: str,
        text: str | None,
        payload: dict,
    ) -> None:
        self.db.add(
            TelegramMessage(
                update_id=update_id,
                chat_id=chat_id,
                telegram_user_id=telegram_user_id,
                direction="INBOUND",
                message_type=message_type,
                text=text,
                payload=payload,
            )
        )

    def _help_text(self) -> str:
        return "\n".join(
            [
                "Available commands:",
                "/start - Open main menu",
                "/hr - HR operations",
                "/site - Site and procurement",
                "/report - Reports",
                "/help - Show this help",
            ]
        )

