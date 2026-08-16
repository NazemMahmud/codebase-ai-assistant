"""Hybrid retrieval: vector + lexical search merged with reciprocal rank fusion."""
from app.services.retrieval.fusion import reciprocal_rank_fusion
from app.services.retrieval.service import retrieve

__all__ = ["retrieve", "reciprocal_rank_fusion"]
