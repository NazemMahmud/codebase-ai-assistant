"""OpenRouter provider — the one wired generation backend (OpenAI-compatible API)."""
from __future__ import annotations

import httpx

from app.config import settings
from app.services.llm.base import LLMError
from app.services.llm.constants import (
    CHAT_COMPLETIONS_PATH,
    MSG_NO_API_KEY,
    MSG_NO_MODEL,
    MSG_REQUEST_FAILED,
    ROLE_SYSTEM,
    ROLE_USER,
)


class OpenRouterProvider:
    """Calls an OpenAI-compatible chat-completions endpoint. BYOK, pinned model."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send system+user messages to the chat-completions API; return the reply text.

        Raises LLMError if the key/model is unset or the request/response fails.
        """
        # todo: separate for single responsibility

        if not settings.LLM_API_KEY:
            raise LLMError(MSG_NO_API_KEY)

        if not settings.LLM_MODEL:
            raise LLMError(MSG_NO_MODEL)

        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": ROLE_SYSTEM, "content": system_prompt},
                {"role": ROLE_USER, "content": user_prompt},
            ],
            "temperature": settings.LLM_TEMPERATURE,
        }
        headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
        url     = f"{settings.LLM_BASE_URL}{CHAT_COMPLETIONS_PATH}"

        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMError(MSG_REQUEST_FAILED.format(detail=exc)) from exc
