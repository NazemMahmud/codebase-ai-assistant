"""Constants for LLM providers."""

# Provider names (match settings.LLM_PROVIDER).
PROVIDER_OPENROUTER = "openrouter"

# OpenAI-style chat message roles.
ROLE_SYSTEM = "system"
ROLE_USER = "user"

# OpenAI-compatible chat-completions path (appended to LLM_BASE_URL).
CHAT_COMPLETIONS_PATH = "/chat/completions"

# Error messages.
MSG_NO_API_KEY = "LLM_API_KEY is not set (BYOK required for generation)."
MSG_NO_MODEL = "LLM_MODEL is not set (pin a model for reproducible answers)."
MSG_UNKNOWN_PROVIDER = "Unknown LLM provider: {provider}"
MSG_REQUEST_FAILED = "LLM request failed: {detail}"
