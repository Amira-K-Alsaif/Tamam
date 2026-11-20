from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_lists_every_procedure(catalog_file):
    response = client.get("/api/procedures")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["reimbursements", "vpn"]


def test_search_ignores_alef_and_taa_marbuta_spelling(catalog_file):
    response = client.get("/api/procedures", params={"q": "تعويض مصاريف"})

    assert [item["id"] for item in response.json()] == ["reimbursements"]


def test_filters_by_department(catalog_file):
    response = client.get("/api/procedures", params={"department": "تقنية المعلومات"})

    assert [item["id"] for item in response.json()] == ["vpn"]


def test_returns_an_empty_list_when_nothing_matches(catalog_file):
    assert client.get("/api/procedures", params={"q": "سفر"}).json() == []


def test_returns_an_empty_list_before_the_catalog_is_extracted(tmp_path, monkeypatch):
    from app.modules.procedures import service

    monkeypatch.setattr(service, "CATALOG_PATH", tmp_path / "missing.json")

    assert client.get("/api/procedures").json() == []


def test_returns_one_procedure_with_its_source(catalog_file):
    response = client.get("/api/procedures/vpn")

    assert response.status_code == 200
    assert response.json()["source"]["document_id"] == "vpn"


def test_unknown_procedure_is_404_in_arabic(catalog_file):
    response = client.get("/api/procedures/nope")

    assert response.status_code == 404
    assert response.json()["detail"] == "ما لقيت هذا الإجراء."
