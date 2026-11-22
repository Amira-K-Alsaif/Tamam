import pytest
from fastapi.testclient import TestClient

from app.ai.llm import LLMNotConfiguredError, LLMUnavailableError
from app.main import app
from app.modules.chat import service
from app.modules.chat.corpus import CorpusNotPreparedError
from app.modules.chat.schemas import AskResponse

client = TestClient(app)


def test_ask_returns_the_service_answer(monkeypatch):
    monkeypatch.setattr(
        service, "answer", lambda question: AskResponse(answer="جواب", found=True, sources=[])
    )

    response = client.post("/api/chat/ask", json={"question": "كم يوم إجازتي؟"})

    assert response.status_code == 200
    assert response.json() == {"answer": "جواب", "found": True, "sources": []}


def test_ask_rejects_an_empty_question():
    response = client.post("/api/chat/ask", json={"question": ""})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "error", [LLMNotConfiguredError, LLMUnavailableError, CorpusNotPreparedError]
)
def test_ask_returns_503_when_the_service_is_not_set_up(monkeypatch, error):
    def not_set_up(question):
        raise error("setup detail the user must not see")

    monkeypatch.setattr(service, "answer", not_set_up)

    response = client.post("/api/chat/ask", json={"question": "كم يوم إجازتي؟"})

    assert response.status_code == 503
    assert "setup detail" not in response.text
