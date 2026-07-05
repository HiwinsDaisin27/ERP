"""Website Management Intelligence assistant — read-only analytics LLM.

Separate from the Telegram insertion client. Uses stronger reasoning models
and read-only analytics tools once the website layer is built.
"""

from app.core.config import settings
from app.services.llm_openrouter import OpenRouterError, chat_completion


class LLMRetrievalClient:
    def __init__(self) -> None:
        self.provider = (settings.llm_retrieval_provider or "openrouter").lower().strip()
        self.model = settings.llm_retrieval_model or "google/gemini-2.5-flash"
        self.fallback_models = settings.llm_retrieval_fallback_models_list

    @property
    def is_configured(self) -> bool:
        return bool(settings.llm_retrieval_api_key or settings.llm_insertion_api_key)

    def _api_key(self) -> str:
        key = settings.llm_retrieval_api_key or settings.llm_insertion_api_key
        if not key:
            raise ValueError("LLM_RETRIEVAL_API_KEY or LLM_INSERTION_API_KEY is required.")
        return key

    async def analyze(self, question: str, tool_schemas: list[dict], entity_context: str | None = None) -> dict:
        """Run a retrieval/analysis turn. Website layer will wire tool execution."""
        if self.provider != "openrouter":
            raise ValueError("Only openrouter is configured for retrieval LLM right now.")

        models = self._model_chain()
        errors: list[str] = []
        tools = [{"type": "function", "function": schema} for schema in tool_schemas]

        system_lines = [
            "You are a construction ERP management intelligence assistant.",
            "Answer using read-only analytics tools. Never invent numbers.",
            "Summarize findings clearly for a contractor or site manager.",
        ]
        if entity_context:
            system_lines.extend(["", "Business context:", entity_context])

        for model in models:
            try:
                return await chat_completion(
                    model=model,
                    messages=[
                        {"role": "system", "content": "\n".join(system_lines)},
                        {"role": "user", "content": question},
                    ],
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.2,
                    api_key=self._api_key(),
                )
            except OpenRouterError as exc:
                errors.append(f"{model}: {exc}")

        raise ValueError("Retrieval LLM failed: " + " | ".join(errors[-3:]))

    def _model_chain(self) -> list[str]:
        chain: list[str] = []
        for model in [self.model, *self.fallback_models]:
            if model and model not in chain:
                chain.append(model)
        return chain
