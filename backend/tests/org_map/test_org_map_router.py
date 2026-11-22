from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_overview():
    response = client.get("/api/org-map/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["my_department_id"] == "dep-data"
    assert len(body["departments"]) == 5


def test_department_and_person():
    department = client.get("/api/org-map/departments/dep-data")
    person = client.get("/api/org-map/people/emp-003")

    assert department.status_code == 200
    assert len(department.json()["members"]) == 6
    assert person.status_code == 200
    assert person.json()["relation"] == "mentor"


def test_unknown_ids_return_404():
    assert client.get("/api/org-map/departments/nope").status_code == 404
    assert client.get("/api/org-map/people/nope").status_code == 404


def test_search():
    response = client.get("/api/org-map/search", params={"q": "طلبات الشراء"})

    assert response.status_code == 200
    assert response.json()["hits"][0]["person"]["full_name"] == "أمل الفيفي"


def test_search_rejects_a_too_short_query():
    assert client.get("/api/org-map/search", params={"q": "a"}).status_code == 422
