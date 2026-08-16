"""Vector search — pgvector cosine similarity over chunk embeddings."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk


def vector_search(
    session: Session,
    query_embedding: list[float],
    codebase_id: uuid.UUID,
    limit: int,
) -> list[uuid.UUID]:
    """Return chunk ids ranked by cosine similarity to the query embedding (best first).

    Scoped to one codebase, excludes soft-deleted chunks and rows without an embedding.
    """
    stmt = (
        select(Chunk.id)
        .where(
            Chunk.codebase_id == codebase_id,
            Chunk.deleted_at.is_(None),
            Chunk.embedding.is_not(None),
        )
        .order_by(Chunk.embedding.cosine_distance(query_embedding))  # ascending = closest
        .limit(limit)
    )
    return list(session.scalars(stmt))
