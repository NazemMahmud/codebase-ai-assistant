"""Chat service — answer a question about one codebase.

Pipeline: verify codebase → retrieve → assemble context → LLM → answer + citations.
Web-agnostic (raises domain errors; the route maps them to HTTP).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.enums import CodebaseStatus
from app.models.codebase import Codebase
from app.services.chat.constants import (
    MSG_CODEBASE_NOT_FOUND,
    MSG_CODEBASE_NOT_READY,
    NOT_FOUND_REPLY,
    SYSTEM_PROMPT,
)
from app.services.chat.context import Citation, assemble_context
from app.services.chat.errors import CodebaseNotFoundError
from app.services.chat.prompts import build_user_prompt
from app.services.llm import get_llm_provider
from app.services.retrieval import retrieve


@dataclass
class ChatAnswer:
    answer: str
    citations: list[Citation]


def answer_question(session: Session, question: str, codebase_id: uuid.UUID) -> ChatAnswer:
    """Answer `question` about `codebase_id`.

    Explicit, non-hallucinated replies for the non-ready cases:
    - codebase missing/deleted → CodebaseNotFoundError (404 at the route)
    - not indexed/ready → a plain status message, no LLM call
    - nothing retrieved → the "not found" reply, no LLM call
    Otherwise: ground the answer in retrieved chunks and cite them.
    """
    # todo: separate code section for single responsibility
    codebase = session.get(Codebase, codebase_id)
    if codebase is None or codebase.deleted_at is not None:
        raise CodebaseNotFoundError(MSG_CODEBASE_NOT_FOUND)

    if codebase.status != CodebaseStatus.READY:
        status = getattr(codebase.status, "value", codebase.status)
        return ChatAnswer(answer=MSG_CODEBASE_NOT_READY.format(status=status), citations=[])

    chunks = retrieve(session, question, codebase_id)
    if not chunks:
        return ChatAnswer(answer=NOT_FOUND_REPLY, citations=[])

    assembled   = assemble_context(chunks)
    user_prompt = build_user_prompt(assembled.text, question)
    answer_text = get_llm_provider().complete(SYSTEM_PROMPT, user_prompt)

    return ChatAnswer(answer=answer_text, citations=assembled.citations)
