from sqlalchemy import select
from sqlalchemy.orm import Session

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
                f"Saved as data submission #{submission.id}, but extraction failed: {submission.error}",
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
