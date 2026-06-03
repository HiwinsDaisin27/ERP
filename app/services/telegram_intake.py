from sqlalchemy.orm import Session

from app.models.telegram import TelegramDataSubmission


class TelegramIntakeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_pending_submission(
        self,
        chat_id: int,
        telegram_user_id: int | None,
        raw_text: str,
    ) -> TelegramDataSubmission:
        submission = TelegramDataSubmission(
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
            raw_text=raw_text,
            status="PENDING_LLM",
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        return submission

