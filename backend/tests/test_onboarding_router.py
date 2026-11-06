from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_me_returns_the_mock_employee():
    response = client.get("/api/onboarding/me")

    assert response.status_code == 200
    assert response.json()["id"] == "emp-004"


def test_roadmap_returns_weeks_in_order():
    response = client.get("/api/onboarding/roadmap")

    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == "emp-004"
    assert [week["week"] for week in body["weeks"]] == [1, 2]
    kinds = {item["kind"] for week in body["weeks"] for item in week["items"]}
    assert kinds == {"lesson", "access", "person"}
