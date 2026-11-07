import pytest

from app.ai import llm, reranker
from app.modules.chat import service

CHUNKS = [
    {
        "id": "a",
        "document_id": "doc-leave",
        "document_title": "سياسة الإجازات",
        "section_title": "الإجازة السنوية",
        "page": 4,
        "text": "إجازة سنوية مدتها ٢١ يوماً.",
    },
    {
        "id": "b",
        "document_id": "doc-remote",
        "document_title": "سياسة العمل عن بعد",
        "section_title": "الأهلية",
        "page": 2,
        "text": "العمل عن بعد يومين في الأسبوع.",
    },
]


@pytest.fixture
def close_chunks(monkeypatch):
    monkeypatch.setattr(service, "retrieve", lambda question: [CHUNKS[0], CHUNKS[1]])
    # Keeps the retrieval order: the first chunk gets the highest score.
    monkeypatch.setattr(
        reranker, "rerank", lambda question, texts: [len(texts) - i for i in range(len(texts))]
    )


def answer_with(monkeypatch, model_text):
    monkeypatch.setattr(llm, "generate", lambda system, user: model_text)
    return service.answer("سؤال")


def test_returns_only_the_cited_sources(monkeypatch, close_chunks):
    result = answer_with(monkeypatch, "إجازتك ٢١ يوماً [1].")

    assert result.found
    assert [source.document_id for source in result.sources] == ["doc-leave"]


def test_uses_the_reranker_order(monkeypatch, close_chunks):
    # The reranker prefers the second chunk, so it becomes source [1].
    monkeypatch.setattr(reranker, "rerank", lambda question, texts: [0.1, 0.9])

    result = answer_with(monkeypatch, "تقدر تشتغل من البيت يومين [1].")

    assert [source.document_id for source in result.sources] == ["doc-remote"]


def test_renumbers_citations_to_match_the_returned_sources(monkeypatch, close_chunks):
    result = answer_with(monkeypatch, "تقدر تشتغل من البيت يومين [2].")

    assert result.answer == "تقدر تشتغل من البيت يومين [1]."
    assert [source.document_id for source in result.sources] == ["doc-remote"]


def test_rejects_an_answer_without_citations(monkeypatch, close_chunks):
    result = answer_with(monkeypatch, "إجازتك ٣٠ يوماً.")

    assert not result.found
    assert result.sources == []


def test_rejects_an_answer_citing_an_unknown_source(monkeypatch, close_chunks):
    result = answer_with(monkeypatch, "إجازتك ٢١ يوماً [1]، وبدل السكن ٥٠٠ ريال [7].")

    assert not result.found


def test_skips_the_model_when_nothing_is_close(monkeypatch):
    monkeypatch.setattr(service, "search", lambda question, k=3: [(0.5, CHUNKS[0])])
    monkeypatch.setattr(service, "keyword_search", lambda question, k=3: [])

    def must_not_call(system, user):
        raise AssertionError("the model should not be called")

    monkeypatch.setattr(llm, "generate", must_not_call)

    assert not service.answer("وش أحسن مطعم؟").found


def test_retrieve_adds_keyword_matches_the_meaning_search_missed(monkeypatch):
    monkeypatch.setattr(service, "search", lambda question, k=3: [(0.9, CHUNKS[0])])
    monkeypatch.setattr(service, "keyword_search", lambda question, k=3: [(2.0, CHUNKS[1])])

    ids = [chunk["id"] for chunk in service.retrieve("VPN")]

    assert set(ids) == {"a", "b"}


def test_retrieve_drops_meaning_matches_below_the_threshold(monkeypatch):
    monkeypatch.setattr(service, "search", lambda question, k=3: [(0.5, CHUNKS[0])])
    monkeypatch.setattr(service, "keyword_search", lambda question, k=3: [(2.0, CHUNKS[1])])

    assert [chunk["id"] for chunk in service.retrieve("VPN")] == ["b"]
