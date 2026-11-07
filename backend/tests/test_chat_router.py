from fastapi.testclient import TestClient

from app.ai.llm import LLMNotConfiguredError
from app.main import app
from app.modules.chat import service
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


def test_ask_returns_503_when_the_model_is_not_configured(monkeypatch):
    def not_configured(question):
        raise LLMNotConfiguredError("missing key")

    monkeypatch.setattr(service, "answer", not_configured)

    response = client.post("/api/chat/ask", json={"question": "كم يوم إجازتي؟"})

    assert response.status_code == 503
