"""LLM providers: one interface, one wired provider, selected by config."""
from app.config import settings
from app.services.llm.base import LLMError, LLMProvider
from app.services.llm.constants import MSG_UNKNOWN_PROVIDER, PROVIDER_OPENROUTER
from app.services.llm.openrouter import OpenRouterProvider

_PROVIDERS = {PROVIDER_OPENROUTER: OpenRouterProvider}


def get_llm_provider() -> LLMProvider:
    """Return the configured provider instance (others slot in behind LLMProvider)."""

    provider_cls = _PROVIDERS.get(settings.LLM_PROVIDER)
    if provider_cls is None:
        raise LLMError(MSG_UNKNOWN_PROVIDER.format(provider=settings.LLM_PROVIDER))

    return provider_cls()


__all__ = ["LLMProvider", "LLMError", "get_llm_provider"]
