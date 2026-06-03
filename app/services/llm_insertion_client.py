import json

import httpx

from app.core.config import settings
from app.services.business_tools import tool_schemas


class LLMInsertionClient:
    def __init__(self) -> None:
        self.provider = (settings.llm_insertion_provider or "").lower()
        self.api_key = settings.llm_insertion_api_key
        self.model = settings.llm_insertion_model

    async def extract_tool_call(self, raw_text: str) -> tuple[str, dict]:
        if self.provider != "openrouter":
            raise ValueError("Only openrouter is configured for insertion LLM right now.")
        if not self.api_key or not self.model:
            raise ValueError("LLM_INSERTION_API_KEY and LLM_INSERTION_MODEL are required.")

        tools = [
            {
                "type": "function",
                "function": schema,
            }
            for schema in tool_schemas()
        ]
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": raw_text,
                },
            ],
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.app_base_url or "http://127.0.0.1:8000",
            "X-Title": settings.app_name,
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        message = data["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            raise ValueError("The LLM did not choose a supported insertion tool.")

        first_call = tool_calls[0]["function"]
        tool_name = first_call["name"]
        arguments = first_call.get("arguments") or "{}"
        if isinstance(arguments, str):
            tool_args = json.loads(arguments)
        else:
            tool_args = arguments

        return tool_name, tool_args

    def _system_prompt(self) -> str:
        return "\n".join(
            [
                "You convert construction site Telegram updates into exactly one backend tool call.",
                "Never answer with prose when a tool call is possible.",
                "Only use the available tools.",
                "Never create payroll, salary, payment approval, or confidential finance records.",
                "If the user asks for payroll or confidential data, do not call a tool.",
                "Dates must be YYYY-MM-DD or today.",
                "Preserve names exactly as written unless only casing changes are needed.",
                "For attendance messages, put names under present_worker_names and absent_worker_names.",
            ]
        )

