"""End-to-end tests of answer(), with retrieval and the language model faked."""

import pytest

from app.ai import llm
from app.modules.chat import retrieval, service
from app.modules.chat.prompts import REWRITE_PROMPT


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


def test_does_not_ask_for_an_answer_when_retrieval_finds_nothing(monkeypatch):
    monkeypatch.setattr(retrieval, "hybrid_search", lambda question: [])

    def rewrite_only(system, user):
        if system != REWRITE_PROMPT:
            raise AssertionError("the model should not be asked for an answer")
        return "أفضل المطاعم"

    monkeypatch.setattr(llm, "generate", rewrite_only)

    assert not service.answer("وش أحسن مطعم؟").found


def test_tells_the_model_which_company_it_works_for(monkeypatch, found):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "company_name", "شركة الواحة")
    prompts_seen = []

    def remember(system, user):
        prompts_seen.append(system)
        return "إجازتك ٢١ يوماً [1]."

    monkeypatch.setattr(llm, "generate", remember)
    service.answer("كم يوم إجازتي؟")

    assert "شركة الواحة" in prompts_seen[-1]


def model_that_rewrites(monkeypatch, rewritten: str, answer: str = "يومان في الأسبوع [1]."):
    def reply(system, user):
        return rewritten if system == REWRITE_PROMPT else answer

    monkeypatch.setattr(llm, "generate", reply)


def test_searches_with_the_dialect_question_and_its_formal_rewrite(monkeypatch, chunks):
    searched, reranked = [], []
    monkeypatch.setattr(retrieval, "hybrid_search", lambda text: searched.append(text) or chunks)
    monkeypatch.setattr(
        retrieval, "rerank", lambda text, candidates, k: reranked.append(text) or candidates[:k]
    )
    model_that_rewrites(monkeypatch, "سياسة العمل عن بعد")

    result = service.answer("أبي أشتغل من البيت")

    assert result.found
    assert set(searched) == {"أبي أشتغل من البيت", "سياسة العمل عن بعد"}
    assert reranked == ["أبي أشتغل من البيت سياسة العمل عن بعد"]


def test_the_rewrite_keeps_only_its_first_line(monkeypatch):
    model_that_rewrites(monkeypatch, "سياسة العمل عن بعد\nوهذا شرح زائد")

    assert service.rewrite("أبي أشتغل من البيت") == "سياسة العمل عن بعد"


def test_an_empty_rewrite_falls_back_to_the_question(monkeypatch):
    model_that_rewrites(monkeypatch, "   ")

    assert service.rewrite("أبي أشتغل من البيت") == "أبي أشتغل من البيت"
