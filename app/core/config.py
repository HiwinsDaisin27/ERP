from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TheSecond Backend"
    environment: str = "development"

    database_url: str = Field(..., validation_alias="DATABASE_URL")

    telegram_bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_admin_chat_id: int | None = Field(None, validation_alias="TELEGRAM_ADMIN_CHAT_ID")
    telegram_webhook_secret: str | None = Field(None, validation_alias="TELEGRAM_WEBHOOK_SECRET")
    public_webhook_base_url: str | None = Field(None, validation_alias="PUBLIC_WEBHOOK_BASE_URL")

    llm_insertion_provider: str | None = Field(None, validation_alias="LLM_INSERTION_PROVIDER")
    llm_insertion_api_key: str | None = Field(None, validation_alias="LLM_INSERTION_API_KEY")
    llm_insertion_model: str | None = Field(None, validation_alias="LLM_INSERTION_MODEL")

    jwt_secret: str | None = Field(None, validation_alias="JWT_SECRET")
    app_base_url: str | None = Field(None, validation_alias="APP_BASE_URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def telegram_webhook_url(self) -> str:
        if not self.public_webhook_base_url:
            raise ValueError("PUBLIC_WEBHOOK_BASE_URL is required to set the Telegram webhook")
        return f"{self.public_webhook_base_url.rstrip('/')}/webhooks/telegram"

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
