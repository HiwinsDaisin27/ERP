import asyncio
import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


def parse_openrouter_error(response: httpx.Response) -> OpenRouterError:
    try:
        body = response.json()
        error = body.get("error", {})
        message = error.get("message") or response.text
        metadata = error.get("metadata") or {}
        retry_after = metadata.get("retry_after_seconds") or metadata.get("retry_after_seconds_raw")
    except Exception:
        message = response.text
        retry_after = None

    return OpenRouterError(
        message,
        status_code=response.status_code,
        retry_after=float(retry_after) if retry_after is not None else None,
    )


async def chat_completion(
    *,
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict | None = None,
    temperature: float = 0,
    max_retries: int = 3,
    api_key: str | None = None,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    resolved_key = api_key or settings.llm_insertion_api_key
    if not resolved_key:
        raise OpenRouterError("An OpenRouter API key is required.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
    if tool_choice is not None:
        payload["tool_choice"] = tool_choice

    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.app_base_url or "http://127.0.0.1:8000",
        "X-Title": settings.app_name,
    }

    last_error: OpenRouterError | None = None
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(OPENROUTER_CHAT_URL, headers=headers, json=payload)

        if response.is_success:
            return response.json()

        error = parse_openrouter_error(response)
        last_error = error

        if response.status_code == 429 and attempt < max_retries - 1:
            wait_seconds = error.retry_after if error.retry_after is not None else min(2 ** attempt, 8)
            if wait_seconds > 10:
                raise error
            logger.warning("OpenRouter rate limit for %s, retrying in %.1fs", model, wait_seconds)
            await asyncio.sleep(wait_seconds)
            continue

        raise error

    raise last_error or OpenRouterError("OpenRouter request failed.")


def extract_first_tool_call(data: dict[str, Any]) -> tuple[str, dict]:
    message = data["choices"][0]["message"]
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        content = (message.get("content") or "").strip()
        raise ValueError(
            "The model did not return a tool call."
            + (f" Response: {content[:200]}" if content else "")
        )

    first_call = tool_calls[0]["function"]
    tool_name = first_call["name"]
    arguments = first_call.get("arguments") or "{}"
    if isinstance(arguments, str):
        tool_args = json.loads(arguments)
    else:
        tool_args = arguments

    return tool_name, tool_args
