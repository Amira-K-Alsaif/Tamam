import pytest
from langchain_core.exceptions import (
    ModelAPIError,
    ModelAuthenticationError,
    ModelRateLimitError,
)

from app.ai import llm
from app.config import get_settings


class Answers:
    def __init__(self, text: str):
        self.text = text

    def invoke(self, messages):
        return self


class Fails:
    def __init__(self, error: Exception):
        self.error = error

    def invoke(self, messages):
        raise self.error


def use_models(monkeypatch, clients: dict, fallback: str = "backup-model"):
    """Points the settings at a main and a fallback model, answered by the given fakes."""
    monkeypatch.setattr(get_settings(), "llm_model", "main-model")
    monkeypatch.setattr(get_settings(), "llm_fallback_model", fallback)
    asked: list[str] = []

    def client(model):
        asked.append(model)
        return clients[model]

    monkeypatch.setattr(llm, "_client", client)
    return asked


def test_the_main_model_answers_when_it_is_available(monkeypatch):
    asked = use_models(monkeypatch, {"main-model": Answers("من الأساسي")})

    assert llm.generate("system", "question") == "من الأساسي"
    assert asked == ["main-model"]


@pytest.mark.parametrize(
    "error",
    [ModelAPIError("503 UNAVAILABLE high demand"), ModelRateLimitError("429 RESOURCE_EXHAUSTED")],
)
def test_the_fallback_model_answers_when_the_main_one_is_busy(monkeypatch, error):
    asked = use_models(
        monkeypatch, {"main-model": Fails(error), "backup-model": Answers("من الاحتياطي")}
    )

    assert llm.generate("system", "question") == "من الاحتياطي"
    assert asked == ["main-model", "backup-model"]


def test_fails_when_both_models_are_busy(monkeypatch):
    use_models(
        monkeypatch,
        {
            "main-model": Fails(ModelAPIError("503")),
            "backup-model": Fails(ModelAPIError("503")),
        },
    )

    with pytest.raises(llm.LLMUnavailableError):
        llm.generate("system", "question")


def test_a_used_up_quota_becomes_a_tamam_error(monkeypatch):
    use_models(
        monkeypatch, {"main-model": Fails(ModelRateLimitError("429 RESOURCE_EXHAUSTED"))}, ""
    )

    with pytest.raises(llm.LLMQuotaExceededError):
        llm.generate("system", "question")


@pytest.mark.parametrize(("fallback", "main_retries"), [("backup-model", 0), ("", 2)])
def test_the_main_model_retries_only_when_nothing_comes_after_it(
    monkeypatch, fallback, main_retries
):
    monkeypatch.setattr(get_settings(), "llm_model", "main-model")
    monkeypatch.setattr(get_settings(), "llm_fallback_model", fallback)
    monkeypatch.setattr(get_settings(), "openrouter_api_key", "test-key")
    llm._client.cache_clear()

    assert llm._client("main-model").max_retries == main_retries
    if fallback:
        assert llm._client("backup-model").max_retries == 2
    llm._client.cache_clear()


def test_an_empty_fallback_asks_only_the_main_model(monkeypatch):
    asked = use_models(monkeypatch, {"main-model": Fails(ModelAPIError("503"))}, fallback="")

    with pytest.raises(llm.LLMUnavailableError):
        llm.generate("system", "question")
    assert asked == ["main-model"]


def test_a_rejected_key_means_the_service_is_not_set_up(monkeypatch):
    use_models(monkeypatch, {"main-model": Fails(ModelAuthenticationError("401 invalid key"))}, "")

    with pytest.raises(llm.LLMNotConfiguredError):
        llm.generate("system", "question")


def test_a_missing_key_means_the_service_is_not_set_up(monkeypatch):
    monkeypatch.setattr(get_settings(), "openrouter_api_key", "")
    llm._client.cache_clear()

    with pytest.raises(llm.LLMNotConfiguredError):
        llm._client("main-model")


def test_the_client_talks_to_openrouter_with_minimal_reasoning(monkeypatch):
    monkeypatch.setattr(get_settings(), "openrouter_api_key", "test-key")
    llm._client.cache_clear()

    client = llm._client("google/gemini-3.6-flash")

    assert str(client.openai_api_base).rstrip("/") == llm.OPENROUTER_URL
    assert client.model_name == "google/gemini-3.6-flash"
    assert client.extra_body == {"reasoning": {"effort": "minimal"}}
    assert client.max_tokens == 8192
    llm._client.cache_clear()


def test_fast_replies_try_the_lighter_model_first(monkeypatch):
    asked = use_models(
        monkeypatch,
        {"light-model": Fails(ModelAPIError("503")), "main-model": Answers("من الأساسي")},
    )
    monkeypatch.setattr(get_settings(), "llm_fast_model", "light-model")

    assert llm.generate("system", "question", fast=True) == "من الأساسي"
    assert asked == ["light-model", "main-model"]


def test_ordinary_replies_skip_the_lighter_model(monkeypatch):
    asked = use_models(monkeypatch, {"main-model": Answers("من الأساسي")})
    monkeypatch.setattr(get_settings(), "llm_fast_model", "light-model")

    llm.generate("system", "question")

    assert asked == ["main-model"]
