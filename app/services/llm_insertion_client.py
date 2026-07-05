import logging

from app.core.config import settings
from app.services.business_tools import tool_schemas
from app.services.llm_openrouter import OpenRouterError, chat_completion, extract_first_tool_call

logger = logging.getLogger(__name__)


class LLMInsertionClient:
    def __init__(self) -> None:
        self.provider = (settings.llm_insertion_provider or "openrouter").lower().strip()
        self.model = settings.llm_insertion_model
        self.fallback_models = settings.llm_insertion_fallback_models_list

    async def extract_tool_call(self, raw_text: str, entity_context: str | None = None) -> tuple[str, dict]:
        if not settings.llm_insertion_api_key:
            raise ValueError("LLM_INSERTION_API_KEY is required. Add your OpenRouter key to .env.")

        if self.provider == "groq":
            return await self._extract_with_groq(raw_text, entity_context)

        if self.provider != "openrouter":
            logger.warning("Unknown LLM_INSERTION_PROVIDER=%s, using openrouter.", self.provider)

        return await self._extract_with_openrouter_chain(raw_text, entity_context)

    async def _extract_with_openrouter_chain(
        self,
        raw_text: str,
        entity_context: str | None,
    ) -> tuple[str, dict]:
        models = self._model_chain()
        errors: list[str] = []

        for model in models:
            try:
                return await self._extract_with_openrouter_model(raw_text, model, entity_context)
            except (OpenRouterError, ValueError) as exc:
                errors.append(f"{model}: {exc}")
                logger.warning("Insertion model failed (%s): %s", model, exc)

        raise ValueError(
            "All insertion models failed. "
            + " | ".join(errors[-3:])
            + ". Try again in a minute or set LLM_INSERTION_MODEL=openrouter/free in .env."
        )

    async def _extract_with_openrouter_model(
        self,
        raw_text: str,
        model: str,
        entity_context: str | None,
    ) -> tuple[str, dict]:
        tools = [{"type": "function", "function": schema} for schema in tool_schemas()]
        data = await chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": self._system_prompt(entity_context)},
                {"role": "user", "content": raw_text},
            ],
            tools=tools,
            tool_choice="required",
            temperature=0,
        )
        return extract_first_tool_call(data)

    async def _extract_with_groq(self, raw_text: str, entity_context: str | None) -> tuple[str, dict]:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_INSERTION_PROVIDER=groq.")

        import httpx

        tools = [{"type": "function", "function": schema} for schema in tool_schemas()]
        model = self.model or "llama-3.3-70b-versatile"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self._system_prompt(entity_context)},
                {"role": "user", "content": raw_text},
            ],
            "tools": tools,
            "tool_choice": "required",
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            if not response.is_success:
                raise ValueError(f"Groq error {response.status_code}: {response.text[:300]}")
            data = response.json()

        return extract_first_tool_call(data)

    def _model_chain(self) -> list[str]:
        chain: list[str] = []
        for model in [self.model, *self.fallback_models, "openrouter/free"]:
            if model and model not in chain:
                chain.append(model)
        return chain

    def _system_prompt(self, entity_context: str | None) -> str:
        lines = [
            "You convert construction site Telegram updates into exactly one backend tool call.",
            "You must always call exactly one tool. Never reply with plain text.",
            "Only use the available tools.",
            "Never create payroll, salary, payment approval, or confidential finance records.",
            "If the user asks for payroll or confidential data, still refuse by returning a progress update with work_completed set to 'Request rejected: payroll is website-only.'",
            "Dates must be YYYY-MM-DD or the literal word today.",
            "Match site_name and worker names to the known entities below when possible.",
            "For attendance messages, put names under present_worker_names and absent_worker_names.",
            "For material receipts, include supplier when mentioned.",
        ]
        if entity_context:
            lines.extend(["", "Known entities:", entity_context])
        return "\n".join(lines)
