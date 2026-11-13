import pytest
from langchain_core.exceptions import ModelRateLimitError

from app.ai import llm


def test_a_used_up_quota_becomes_a_tamam_error(monkeypatch):
    class QuotaUsedUp:
        def invoke(self, messages):
            raise ModelRateLimitError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(llm, "_client", lambda: QuotaUsedUp())

    with pytest.raises(llm.LLMUnavailableError):
        llm.generate("system", "question")
