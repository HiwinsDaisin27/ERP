import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth import AssistantChatMessage
from app.services.analytics_tools import AnalyticsTools, analytics_tool_schemas
from app.services.llm_openrouter import OpenRouterError, chat_completion

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 6


class IntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tools = AnalyticsTools(db)

    async def ask(self, question: str, user_id: int) -> dict:
        if not settings.llm_retrieval_api_key and not settings.llm_insertion_api_key:
            raise ValueError("LLM_RETRIEVAL_API_KEY or LLM_INSERTION_API_KEY is required for the assistant.")

        api_key = settings.llm_retrieval_api_key or settings.llm_insertion_api_key
        models = self._model_chain()
        tool_defs = [{"type": "function", "function": schema} for schema in analytics_tool_schemas()]
        entity_context = self.tools.build_entity_context()

        system_prompt = "\n".join(
            [
                "You are the Management Intelligence assistant for a construction contractor ERP.",
                "Use read-only analytics tools to gather real data before answering.",
                "Never invent numbers. If data is missing, say so clearly.",
                "Write in plain English for a contractor or site manager.",
                "When the user asks for a report, spreadsheet, or export, call export_report_sheet with format xlsx unless they ask for csv.",
                "After exporting, tell the user they can download the file and open XLSX directly in Google Sheets.",
                "You may call multiple tools before giving the final answer.",
                "",
                "Known business entities:",
                entity_context,
            ]
        )

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        tools_used: list[str] = []
        exports: list[dict] = []
        last_error: str | None = None

        for model in models:
            try:
                result = await self._run_with_model(model, messages, tool_defs, api_key, user_id, tools_used, exports)
                self._save_exchange(user_id, question, result)
                return result
            except (OpenRouterError, ValueError) as exc:
                last_error = str(exc)
                logger.warning("Retrieval model %s failed: %s", model, exc)

        raise ValueError(last_error or "Assistant could not complete the request.")

    def _save_exchange(self, user_id: int, question: str, result: dict) -> None:
        self.db.add(
            AssistantChatMessage(
                user_id=user_id,
                role="user",
                text=question,
            )
        )
        self.db.add(
            AssistantChatMessage(
                user_id=user_id,
                role="assistant",
                text=result["answer"],
                tools_used=result["tools_used"],
                exports=result["exports"],
            )
        )
        self.db.commit()

    async def _run_with_model(
        self,
        model: str,
        messages: list[dict],
        tool_defs: list[dict],
        api_key: str,
        user_id: int,
        tools_used: list[str],
        exports: list[dict],
    ) -> dict:
        working_messages = list(messages)

        for _ in range(MAX_TOOL_ROUNDS):
            data = await chat_completion(
                model=model,
                messages=working_messages,
                tools=tool_defs,
                tool_choice="auto",
                temperature=0.2,
                api_key=api_key,
            )
            message = data["choices"][0]["message"]
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                answer = (message.get("content") or "").strip()
                if not answer:
                    answer = self._fallback_answer_from_tools(working_messages)
                if not answer:
                    raise ValueError("The assistant returned an empty response.")
                return {"answer": answer, "tools_used": tools_used, "exports": exports}

            working_messages.append(message)
            for call in tool_calls:
                function = call["function"]
                tool_name = function["name"]
                raw_args = function.get("arguments") or "{}"
                arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                tools_used.append(tool_name)

                try:
                    result = self.tools.call_tool(tool_name, arguments, user_id)
                except Exception as exc:
                    result = {"error": str(exc)}

                if tool_name == "export_report_sheet" and "download_url" in result:
                    exports.append(result)

                working_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(result),
                    }
                )

        raise ValueError("Assistant needed too many tool steps. Try a simpler question.")

    def _fallback_answer_from_tools(self, messages: list[dict]) -> str:
        tool_payloads: list[str] = []
        for message in reversed(messages):
            if message.get("role") != "tool":
                continue
            content = message.get("content") or ""
            if content and '"error"' not in content:
                tool_payloads.append(content)
            if len(tool_payloads) >= 2:
                break
        if not tool_payloads:
            return ""
        return (
            "Here is a summary based on the data retrieved from your ERP:\n\n"
            + "\n\n".join(tool_payloads[:2])
        )

    def _model_chain(self) -> list[str]:
        chain: list[str] = []
        primary = settings.llm_retrieval_model or "openrouter/free"
        fallbacks = settings.llm_retrieval_fallback_models_list or [
            "google/gemini-2.5-flash-lite",
            "openrouter/free",
        ]
        for model in [primary, *fallbacks, "openrouter/free"]:
            if model and model not in chain:
                chain.append(model)
        return chain
