from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.modules.chat import retrieval


def start_server(monkeypatch, warm_up_models: bool) -> list[str]:
    calls: list[str] = []
    monkeypatch.setattr(retrieval, "warm_up", lambda: calls.append("warm_up"))
    monkeypatch.setattr(get_settings(), "warm_up_models", warm_up_models)

    # Entering the client runs the app's startup, as uvicorn does.
    with TestClient(create_app()):
        pass
    return calls


def test_loads_the_models_at_startup_when_enabled(monkeypatch):
    assert start_server(monkeypatch, warm_up_models=True) == ["warm_up"]


def test_skips_loading_the_models_by_default(monkeypatch):
    assert start_server(monkeypatch, warm_up_models=False) == []
