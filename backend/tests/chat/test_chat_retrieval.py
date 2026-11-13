from app.ai import reranker
from app.modules.chat import retrieval


def test_hybrid_search_adds_keyword_matches_the_meaning_search_missed(monkeypatch, leave, remote):
    monkeypatch.setattr(retrieval, "semantic_search", lambda question, k: [(0.9, leave)])
    monkeypatch.setattr(retrieval, "keyword_search", lambda question, k: [(2.0, remote)])

    assert {chunk.id for chunk in retrieval.hybrid_search("VPN")} == {"leave", "remote"}


def test_hybrid_search_drops_meaning_matches_below_the_threshold(monkeypatch, leave, remote):
    monkeypatch.setattr(retrieval, "semantic_search", lambda question, k: [(0.5, leave)])
    monkeypatch.setattr(retrieval, "keyword_search", lambda question, k: [(2.0, remote)])

    assert [chunk.id for chunk in retrieval.hybrid_search("VPN")] == ["remote"]


def test_hybrid_search_returns_nothing_when_nothing_matches(monkeypatch, leave):
    monkeypatch.setattr(retrieval, "semantic_search", lambda question, k: [(0.5, leave)])
    monkeypatch.setattr(retrieval, "keyword_search", lambda question, k: [])

    assert retrieval.hybrid_search("وش أحسن مطعم؟") == []


def test_rerank_orders_by_the_reranker_and_keeps_the_top_k(monkeypatch, chunks, remote):
    monkeypatch.setattr(reranker, "rerank", lambda question, texts: [0.1, 0.9])

    assert retrieval.rerank("أبي أشتغل من البيت", chunks, k=1) == [remote]
