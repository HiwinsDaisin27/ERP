from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.telegram import TelegramMessage, TelegramUser
from app.services.insertion_processor import (
    InsertionProcessor,
    confirmation_keyboard,
    format_extraction_summary,
)
from app.services.telegram_client import TelegramClient
from app.services.telegram_keyboards import (
    intake_examples_text,
    main_menu_keyboard,
    reports_menu_keyboard,
)
from app.services.telegram_intake import TelegramIntakeService
from app.services.workflow_engine import WorkflowEngine

KNOWN_COMMANDS = {"/start", "/report", "/sites", "/workers", "/examples", "/help", "/cancel"}
PAYROLL_HINTS = ("payroll", "salary", " wage", " wages", "payment approved", "mark paid", "pay worker")


class TelegramUpdateHandler:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.telegram = TelegramClient()
        self.workflow_engine = WorkflowEngine(db)
        self.intake = TelegramIntakeService(db)
        self.insertion_processor = InsertionProcessor(db)

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
        if not self._is_allowed_user(from_user):
            await self.telegram.send_message(chat_id, "This bot is restricted to approved site supervisors.")
            return
        text = message.get("text", "")

        self._upsert_user(from_user, chat_id)
        self._log_message(update_id, chat_id, from_user.get("id"), "text", text, payload)
        self.db.commit()

        command = text.strip().split()[0].lower() if text else ""

        if command in {"/start", "start"}:
            self.workflow_engine.cancel_active(chat_id)
            self.db.commit()
            await self.telegram.send_message(chat_id, self._start_text(), main_menu_keyboard())
        elif command == "/report":
            self.workflow_engine.cancel_active(chat_id)
            self.db.commit()
            await self.telegram.send_message(chat_id, "Reports:", reports_menu_keyboard())
        elif command == "/sites":
            await self.telegram.send_message(chat_id, self.workflow_engine.list_sites())
        elif command == "/workers":
            await self.telegram.send_message(chat_id, self.workflow_engine.list_workers())
        elif command == "/examples":
            await self.telegram.send_message(chat_id, intake_examples_text())
        elif command == "/help":
            await self.telegram.send_message(chat_id, self._help_text())
        elif command == "/cancel":
            self.workflow_engine.cancel_active(chat_id)
            self.db.commit()
            await self.telegram.send_message(chat_id, "Cancelled. Send a new site update anytime.", main_menu_keyboard())
        elif text.strip().startswith("/"):
            await self.telegram.send_message(
                chat_id,
                "Unknown command. Use /help for available commands, or send a plain-text site update.",
                main_menu_keyboard(),
            )
        elif not text.strip():
            await self.telegram.send_message(chat_id, "Send a site update as plain text.", main_menu_keyboard())
        elif self._looks_like_payroll_request(text):
            await self.telegram.send_message(
                chat_id,
                "Payroll and payment operations are handled only in the secure website payroll section.",
                main_menu_keyboard(),
            )
        else:
            submission = self.intake.create_pending_submission(chat_id, from_user.get("id"), text)
            submission = await self.insertion_processor.extract_submission(submission)
            if submission.status == "AWAITING_CONFIRMATION":
                await self.telegram.send_message(
                    chat_id,
                    format_extraction_summary(submission),
                    confirmation_keyboard(submission.id),
                )
                return

            await self.telegram.send_message(
                chat_id,
                self._llm_failure_message(submission),
                main_menu_keyboard(),
            )

    def _looks_like_payroll_request(self, text: str) -> bool:
        lowered = text.lower()
        return any(hint in lowered for hint in PAYROLL_HINTS)

    def _llm_failure_message(self, submission) -> str:
        error = submission.error or "Unknown extraction error."
        if "LLM_INSERTION_API_KEY" in error:
            return "LLM is not configured on the server. Ask the admin to set LLM_INSERTION_API_KEY in .env."
        if "429" in error or "rate-limited" in error.lower() or "All insertion models failed" in error:
            return (
                f"Submission #{submission.id} was saved, but the AI service is busy right now.\n"
                f"Details: {error}\n\n"
                "Try again in a minute. The admin can also set LLM_INSERTION_MODEL=openrouter/free in .env."
            )
        return f"Submission #{submission.id} was saved, but extraction failed:\n{error}"

    async def _handle_callback(self, update_id: int, callback_query: dict, payload: dict) -> None:
        from_user = callback_query.get("from", {})
        message = callback_query.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        data = callback_query.get("data", "")

        if chat_id is None:
            return
        if not self._is_allowed_user(from_user):
            await self.telegram.send_message(chat_id, "This bot is restricted to approved site supervisors.")
            return

        self._upsert_user(from_user, chat_id)
        self._log_message(update_id, chat_id, from_user.get("id"), "callback_query", data, payload)
        self.db.commit()

        if data == "menu:main":
            self.workflow_engine.cancel_active(chat_id)
            self.db.commit()
            await self.telegram.send_message(chat_id, self._start_text(), main_menu_keyboard())
        elif data == "menu:reports":
            self.workflow_engine.cancel_active(chat_id)
            self.db.commit()
            await self.telegram.send_message(chat_id, "Reports:", reports_menu_keyboard())
        elif data == "menu:help":
            await self.telegram.send_message(chat_id, self._help_text())
        elif data == "intake:examples":
            await self.telegram.send_message(chat_id, intake_examples_text())
        elif data == "lookup:sites":
            await self.telegram.send_message(chat_id, self.workflow_engine.list_sites())
        elif data == "lookup:workers":
            await self.telegram.send_message(chat_id, self.workflow_engine.list_workers())
        elif data == "report:attendance_daily":
            await self.telegram.send_message(chat_id, self.workflow_engine.report_daily_attendance())
        elif data == "report:site_daily":
            await self.telegram.send_message(chat_id, self.workflow_engine.report_daily_site())
        elif data == "report:payroll_weekly":
            await self.telegram.send_message(chat_id, "Payroll is handled only inside the secure website payroll section.")
        elif data.startswith("submission:confirm:"):
            submission_id = int(data.rsplit(":", 1)[1])
            try:
                submission = self.insertion_processor.confirm_submission(submission_id, chat_id)
            except ValueError as exc:
                await self.telegram.send_message(chat_id, str(exc), main_menu_keyboard())
                return

            if submission.status == "COMPLETED":
                await self.telegram.send_message(
                    chat_id,
                    f"Submission #{submission.id} written successfully.\nResult: {submission.tool_result}",
                    main_menu_keyboard(),
                )
            else:
                await self.telegram.send_message(
                    chat_id,
                    f"Submission #{submission.id} failed during tool execution: {submission.error}",
                    main_menu_keyboard(),
                )
        elif data.startswith("submission:reject:"):
            submission_id = int(data.rsplit(":", 1)[1])
            try:
                submission = self.insertion_processor.reject_submission(submission_id, chat_id)
            except ValueError as exc:
                await self.telegram.send_message(chat_id, str(exc), main_menu_keyboard())
                return
            await self.telegram.send_message(
                chat_id,
                f"Submission #{submission.id} rejected. Nothing was written.",
                main_menu_keyboard(),
            )
        else:
            await self.telegram.send_message(
                chat_id,
                "That action is only available from the secure website.",
                main_menu_keyboard(),
            )

    def _is_allowed_user(self, from_user: dict) -> bool:
        allowed_ids = settings.telegram_allowed_user_ids_set
        if not allowed_ids:
            return True
        telegram_user_id = from_user.get("id")
        return telegram_user_id in allowed_ids

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
                "/start - Show intake menu",
                "/examples - Show data entry examples",
                "/report - Daily reports",
                "/sites - List site IDs",
                "/workers - List worker IDs",
                "/help - Show this help",
                "",
                "Send attendance, material, expense, or progress updates as plain text. Payroll is not accepted through Telegram.",
            ]
        )

    def _start_text(self) -> str:
        return "\n".join(
            [
                "Telegram is now the field data intake channel.",
                "Send attendance, material, expense, or progress updates as plain text.",
                "Payroll and confidential operations stay inside the secure website.",
            ]
        )
