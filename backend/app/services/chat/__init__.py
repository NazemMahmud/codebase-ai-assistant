"""Chat support: context assembly + prompts (the answer service lands in feat/7)."""
from app.services.chat.context import AssembledContext, Citation, assemble_context
from app.services.chat.errors import CodebaseNotFoundError
from app.services.chat.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.chat.service import ChatAnswer, answer_question

__all__ = [
    "AssembledContext",
    "Citation",
    "assemble_context",
    "SYSTEM_PROMPT",
    "build_user_prompt",
    "ChatAnswer",
    "answer_question",
    "CodebaseNotFoundError",
]
