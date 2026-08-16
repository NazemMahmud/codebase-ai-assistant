"""Unit tests for reciprocal rank fusion (pure — no DB)."""
import uuid

from app.services.retrieval.fusion import reciprocal_rank_fusion

A = uuid.UUID(int=1)
B = uuid.UUID(int=2)
C = uuid.UUID(int=3)
D = uuid.UUID(int=4)


def test_empty_lists_return_empty():
    assert reciprocal_rank_fusion([], k=60, top_k=10) == []
    assert reciprocal_rank_fusion([[], []], k=60, top_k=10) == []


def test_single_list_preserves_order():
    assert reciprocal_rank_fusion([[A, B, C]], k=60, top_k=10) == [A, B, C]


def test_item_in_multiple_lists_ranks_higher():
    # B appears in both lists -> should beat A/C which appear once.
    fused = reciprocal_rank_fusion([[A, B], [B, C]], k=60, top_k=10)
    assert fused[0] == B
    assert set(fused) == {A, B, C}


def test_top_k_truncates():
    fused = reciprocal_rank_fusion([[A, B, C, D]], k=60, top_k=2)
    assert fused == [A, B]


def test_score_math_and_ordering():
    # k=1: list1 gives A=1/2, B=1/3; list2 gives B=1/2, A=1/3
    # A = 1/2 + 1/3 = 0.833..., B = 1/3 + 1/2 = 0.833... -> tie; C only in list2 rank2 = 1/3
    fused = reciprocal_rank_fusion([[A, B], [B, A, C]], k=1, top_k=3)
    assert set(fused[:2]) == {A, B}   # A and B tie above C
    assert fused[2] == C
