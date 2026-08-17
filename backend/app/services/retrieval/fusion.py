"""Reciprocal Rank Fusion — merge several ranked id lists into one."""
from __future__ import annotations

import uuid


def reciprocal_rank_fusion(
    ranked_lists: list[list[uuid.UUID]], k: int, top_k: int
) -> list[uuid.UUID]:
    """Fuse ranked lists via RRF and return the top_k ids.

    Each id scores `sum(1 / (k + rank))` across the lists it appears in (rank is 1-based).
    Ids in more lists / higher up rank better.
    `k` dampens the weight of top positions (standard value 60).
    """

    scores: dict[uuid.UUID, float] = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    ordered = sorted(scores, key=lambda cid: scores[cid], reverse=True)

    return ordered[:top_k]
