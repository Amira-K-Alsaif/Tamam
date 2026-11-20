"""Review endpoints are registered under the existing admin-protected router."""

from fastapi.testclient import TestClient

from app.main import app


def test_admin_only_review_endpoints():
    paths = app.openapi()["paths"]
    client = TestClient(app)
    for suffix in ("conflicts", "quality", "alerts"):
        path = f"/api/knowledge/{suffix}"
        assert "get" in paths[path]
        assert client.get(path).status_code == 401
