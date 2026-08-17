"""Lexical search — Postgres full-text (content_tsv) + pg_trgm (symbol_name)."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.services.retrieval.constants import (
    FTS_CONFIG,
    FTS_MATCH_OP,
    SYMBOL_SIMILARITY_THRESHOLD,
)


def fulltext_search(
    session: Session, query: str, codebase_id: uuid.UUID, limit: int
) -> list[uuid.UUID]:
    """Return chunk ids ranked by full-text relevance over `content_tsv`.

    `content_tsv` is a generated column ('simple' config);
    the query uses websearch_to_tsquery so user input is parsed forgiving-ly.
    """
    tsquery = func.websearch_to_tsquery(FTS_CONFIG, query)

    stmt = (
        select(Chunk.id)
        .where(
            Chunk.codebase_id == codebase_id,
            Chunk.deleted_at.is_(None),
            Chunk.content_tsv.op(FTS_MATCH_OP)(tsquery),
        )
        .order_by(func.ts_rank_cd(Chunk.content_tsv, tsquery).desc())
        .limit(limit)
    )

    return list(session.scalars(stmt))


def symbol_search(
    session: Session, query: str, codebase_id: uuid.UUID, limit: int
) -> list[uuid.UUID]:
    """Return chunk ids ranked by trigram similarity of `symbol_name` to the query.

    Catches exact/near identifiers (e.g. `processPayment`) that embeddings miss.
    """
    similarity = func.similarity(Chunk.symbol_name, query)
    stmt = (
        select(Chunk.id)
        .where(
            Chunk.codebase_id == codebase_id,
            Chunk.deleted_at.is_(None),
            Chunk.symbol_name.is_not(None),
            similarity > SYMBOL_SIMILARITY_THRESHOLD,
        )
        .order_by(similarity.desc())
        .limit(limit)
    )

    return list(session.scalars(stmt))
