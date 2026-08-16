"""Hybrid retrieval — embed query, run vector + lexical searches, fuse, load chunks."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chunk import Chunk
from app.services.embedding import embedder
from app.services.retrieval.fusion import reciprocal_rank_fusion
from app.services.retrieval.lexical import fulltext_search, symbol_search
from app.services.retrieval.vector import vector_search


def retrieve(
    session: Session,
    query: str,
    codebase_id: uuid.UUID,
    top_k: int | None = None,
) -> list[Chunk]:
    """Return the top_k most relevant chunks for `query` within one codebase.

    Runs three ranked searches — vector (semantic), full-text, and symbol trigram —
    and merges them with reciprocal rank fusion.
    """

    top_k           = top_k or settings.CONTEXT_MAX_CHUNKS
    query_embedding = embedder.embed_text(query)
    vector_ids      = vector_search(session, query_embedding, codebase_id, settings.VECTOR_TOP_K)
    fulltext_ids    = fulltext_search(session, query, codebase_id, settings.KEYWORD_TOP_K)
    symbol_ids      = symbol_search(session, query, codebase_id, settings.KEYWORD_TOP_K)

    fused_ids = reciprocal_rank_fusion(
        [vector_ids, fulltext_ids, symbol_ids], settings.RRF_K, top_k
    )

    return _load_chunks(session, fused_ids)


def _load_chunks(session: Session, ids: list[uuid.UUID]) -> list[Chunk]:
    """Load chunks by id, preserving the fused order (SQL `IN` doesn't)."""

    if not ids:
        return []

    rows  = session.scalars(select(Chunk).where(Chunk.id.in_(ids))).all()
    by_id = {chunk.id: chunk for chunk in rows}

    return [by_id[cid] for cid in ids if cid in by_id]
