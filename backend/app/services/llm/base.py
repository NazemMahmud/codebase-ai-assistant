"""LLM provider interface — one method the pipeline depends on."""
from __future__ import annotations

from typing import Protocol


class LLMError(RuntimeError):
    """The LLM request failed (missing key/model, HTTP error, bad response)."""


class LLMProvider(Protocol):
    """Any generation backend. Add a provider by implementing this + registering it.

    Kept to a single synchronous `complete` for the slice; streaming is deferred.
    """

    def complete(self, system_prompt: str, user_prompt: str) -> str: ...
