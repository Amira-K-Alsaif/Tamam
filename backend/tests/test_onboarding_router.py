import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.usefixtures("employees_assessed")

client = TestClient(app)


def test_me_returns_the_mock_employee():
    response = client.get("/api/onboarding/me")

    assert response.status_code == 200
    assert response.json()["id"] == "emp-004"


def test_me_includes_the_direct_managers_name():
    body = client.get("/api/onboarding/me").json()

    assert body["manager_id"] == "emp-002"
    assert body["manager_name"] == "سارة القحطاني"


def test_roadmap_returns_weeks_in_order():
    response = client.get("/api/onboarding/roadmap")

    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == "emp-004"
    assert [week["week"] for week in body["weeks"]] == [1, 2]
    kinds = {item["kind"] for week in body["weeks"] for item in week["items"]}
    assert kinds == {"lesson", "access", "person"}
