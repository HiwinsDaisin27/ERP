from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.telegram import TelegramDataSubmission
from app.services.business_tools import BusinessTools
from app.services.llm_insertion_client import LLMInsertionClient


class InsertionProcessor:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.llm = LLMInsertionClient()
        self.tools = BusinessTools(db)

    async def extract_submission(self, submission: TelegramDataSubmission) -> TelegramDataSubmission:
        try:
            tool_name, arguments = await self.llm.extract_tool_call(submission.raw_text)
        except Exception as exc:
            submission.status = "LLM_FAILED"
            submission.error = str(exc)
            submission.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(submission)
            return submission

        submission.status = "AWAITING_CONFIRMATION"
        submission.detected_intent = tool_name
        submission.tool_name = tool_name
        submission.extracted_payload = arguments
        submission.error = None
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def confirm_submission(self, submission_id: int, chat_id: int) -> TelegramDataSubmission:
        submission = self._require_submission(submission_id, chat_id)
        if submission.status != "AWAITING_CONFIRMATION":
            raise ValueError(f"Submission #{submission.id} is not awaiting confirmation.")
        if not submission.tool_name or not submission.extracted_payload:
            raise ValueError(f"Submission #{submission.id} has no extracted tool call.")

        try:
            result = self.tools.call_tool(submission.tool_name, submission.extracted_payload)
        except Exception as exc:
            self.db.rollback()
            submission = self._require_submission(submission_id, chat_id)
            submission.status = "TOOL_FAILED"
            submission.error = str(exc)
            submission.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(submission)
            return submission

        submission.status = "COMPLETED"
        submission.tool_result = result
        submission.error = None
        submission.processed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def reject_submission(self, submission_id: int, chat_id: int) -> TelegramDataSubmission:
        submission = self._require_submission(submission_id, chat_id)
        submission.status = "REJECTED"
        submission.processed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(submission)
        return submission

    def _require_submission(self, submission_id: int, chat_id: int) -> TelegramDataSubmission:
        submission = self.db.get(TelegramDataSubmission, submission_id)
        if submission is None or submission.chat_id != chat_id:
            raise ValueError(f"Submission #{submission_id} was not found.")
        return submission


def confirmation_keyboard(submission_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Confirm Write", "callback_data": f"submission:confirm:{submission_id}"},
                {"text": "Reject", "callback_data": f"submission:reject:{submission_id}"},
            ],
        ]
    }


def format_extraction_summary(submission: TelegramDataSubmission) -> str:
    return "\n".join(
        [
            f"Submission #{submission.id} extracted.",
            f"Tool: {submission.tool_name}",
            "Payload:",
            str(submission.extracted_payload),
            "",
            "Confirm only if this looks correct.",
        ]
    )

