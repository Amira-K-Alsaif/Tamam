"""End-to-end tests of answer(), with retrieval and the language model faked."""

import pytest

from app.ai import llm
from app.modules.chat import retrieval, service


@pytest.fixture
def found(monkeypatch, chunks):
    """Retrieval finds both test chunks, and the reranker keeps their order."""
    monkeypatch.setattr(retrieval, "hybrid_search", lambda question: chunks)
    monkeypatch.setattr(retrieval, "rerank", lambda question, candidates, k: candidates[:k])


def answer_with(monkeypatch, model_text: str):
    monkeypatch.setattr(llm, "generate", lambda system, user: model_text)
    return service.answer("سؤال")


def test_returns_the_answer_with_only_the_cited_sources(monkeypatch, found):
    result = answer_with(monkeypatch, "إجازتك ٢١ يوماً [1].")

    assert result.found
    assert [source.document_id for source in result.sources] == ["doc-leave"]


def test_renumbers_citations_to_match_the_returned_sources(monkeypatch, found):
    result = answer_with(monkeypatch, "تقدر تشتغل من البيت يومين [2].")

    assert result.answer == "تقدر تشتغل من البيت يومين [1]."
    assert [source.document_id for source in result.sources] == ["doc-remote"]


def test_says_not_found_when_the_model_cites_nothing(monkeypatch, found):
    result = answer_with(monkeypatch, "لا توجد إجابة")

    assert not result.found
    assert result.answer == service.NOT_FOUND
    assert result.sources == []


def test_says_not_found_when_the_model_invents_a_source(monkeypatch, found):
    result = answer_with(monkeypatch, "إجازتك ٢١ يوماً [1]، وبدل السكن ٥٠٠ ريال [7].")

    assert not result.found


def test_skips_the_model_when_retrieval_finds_nothing(monkeypatch):
    monkeypatch.setattr(retrieval, "hybrid_search", lambda question: [])

    def must_not_call(system, user):
        raise AssertionError("the model should not be called")

    monkeypatch.setattr(llm, "generate", must_not_call)

    assert not service.answer("وش أحسن مطعم؟").found
