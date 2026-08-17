"""Context assembly — pack retrieved chunks under a token budget with citations.

Whole chunks only (never string-truncate code); capped by count upstream (retrieve returns top_k)
and by a token budget here.
Each chunk is fenced and labelled with its `file:line` so the model can cite it and treat it as data.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.models.chunk import Chunk
from app.services.chat.constants import CHARS_PER_TOKEN, CODE_FENCE


@dataclass
class Citation:
    file_path: str
    start_line: int | None
    end_line: int | None
    symbol_name: str | None


@dataclass
class AssembledContext:
    text: str
    citations: list[Citation]


def assemble_context(chunks: list[Chunk]) -> AssembledContext:
    """Format chunks into one context string + citations, under the token budget."""
    blocks: list[str] = []
    citations: list[Citation] = []
    used_tokens = 0

    for index, chunk in enumerate(chunks, start=1):
        block  = _format_chunk(index, chunk)
        tokens = _estimate_tokens(block)

        # Always include at least one chunk; then stop before blowing the budget.
        if blocks and used_tokens + tokens > settings.CONTEXT_TOKEN_BUDGET:
            break

        blocks.append(block)
        citations.append(_citation(chunk))
        used_tokens += tokens

    return AssembledContext(text="\n\n".join(blocks), citations=citations)


def _format_chunk(index: int, chunk: Chunk) -> str:
    """Render one chunk as a labelled, fenced block: `[n] file:start-end (type name)` + code."""
    location = f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
    header   = f"[{index}] {location}"

    if chunk.symbol_name:
        symbol_type = chunk.symbol_type or "symbol"
        header += f" ({symbol_type} {chunk.symbol_name})"

    language = chunk.programming_language or ""

    return f"{header}\n{CODE_FENCE}{language}\n{chunk.content}\n{CODE_FENCE}"


def _citation(chunk: Chunk) -> Citation:
    """Extract the source reference (file/lines/symbol) for one chunk."""
    return Citation(
        file_path=chunk.file_path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        symbol_name=chunk.symbol_name,
    )


def _estimate_tokens(text: str) -> int:
    """Rough token count without a tokenizer dependency (~4 chars/token)."""
    return len(text) // CHARS_PER_TOKEN + 1
