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
    telegram_allowed_user_ids: str | None = Field(None, validation_alias="TELEGRAM_ALLOWED_USER_IDS")
    public_webhook_base_url: str | None = Field(None, validation_alias="PUBLIC_WEBHOOK_BASE_URL")

    llm_insertion_provider: str | None = Field(None, validation_alias="LLM_INSERTION_PROVIDER")
    llm_insertion_api_key: str | None = Field(None, validation_alias="LLM_INSERTION_API_KEY")
    llm_insertion_model: str | None = Field(None, validation_alias="LLM_INSERTION_MODEL")
    llm_insertion_fallback_models: str | None = Field(None, validation_alias="LLM_INSERTION_FALLBACK_MODELS")

    groq_api_key: str | None = Field(None, validation_alias="GROQ_API_KEY")

    llm_retrieval_provider: str | None = Field(None, validation_alias="LLM_RETRIEVAL_PROVIDER")
    llm_retrieval_api_key: str | None = Field(None, validation_alias="LLM_RETRIEVAL_API_KEY")
    llm_retrieval_model: str | None = Field(None, validation_alias="LLM_RETRIEVAL_MODEL")
    llm_retrieval_fallback_models: str | None = Field(None, validation_alias="LLM_RETRIEVAL_FALLBACK_MODELS")

    jwt_secret: str | None = Field(None, validation_alias="JWT_SECRET")
    app_base_url: str | None = Field(None, validation_alias="APP_BASE_URL")
    frontend_origins: str | None = Field(None, validation_alias="FRONTEND_ORIGINS")
    report_export_dir: str = Field(default="data/exports", validation_alias="REPORT_EXPORT_DIR")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def llm_insertion_fallback_models_list(self) -> list[str]:
        raw = self.llm_insertion_fallback_models or "google/gemini-2.5-flash-lite"
        return [model.strip() for model in raw.split(",") if model.strip()]

    @property
    def llm_retrieval_fallback_models_list(self) -> list[str]:
        raw = self.llm_retrieval_fallback_models or "google/gemini-2.5-flash-lite,openrouter/free"
        return [model.strip() for model in raw.split(",") if model.strip()]

    @property
    def telegram_allowed_user_ids_set(self) -> set[int]:
        raw = self.telegram_allowed_user_ids or ""
        user_ids: set[int] = set()
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            user_ids.add(int(item))
        return user_ids

    @property
    def frontend_origin_list(self) -> list[str]:
        defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
        raw = self.frontend_origins or ""
        configured = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
        return [*defaults, *configured]

    @property
    def llm_insertion_ready(self) -> bool:
        if (self.llm_insertion_provider or "openrouter").lower() == "groq":
            return bool(self.groq_api_key)
        return bool(self.llm_insertion_api_key)

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
