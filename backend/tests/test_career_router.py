import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.career import repository, service
from app.modules.career.repository import get_repository

client = TestClient(app)
ACCOUNTANT, FINANCE_MANAGER = 7, 8


@pytest.fixture(autouse=True)
def json_data_only(monkeypatch):
    """Tests read the committed JSON files, never a developer's Supabase."""
    monkeypatch.setattr(repository, "get_supabase", lambda: None)
    get_repository.cache_clear()
    yield
    get_repository.cache_clear()


def test_titles_lists_the_ten_titles_with_their_next_step():
    titles = client.get("/api/career/titles").json()
    assert len(titles) == 12
    accountant = next(t for t in titles if t["id"] == ACCOUNTANT)
    assert accountant["next_title_id"] == FINANCE_MANAGER
    assert accountant["postings_count"] > 0


def test_title_skills_are_frequencies():
    skills = client.get(f"/api/career/titles/{FINANCE_MANAGER}/skills").json()
    assert skills
    assert all(0 <= s["frequency"] <= 1 for s in skills)


def test_unknown_title_is_404():
    assert client.get("/api/career/titles/999/skills").status_code == 404
    response = client.get("/api/career/gap-analysis?current_title_id=999&target_title_id=8")
    assert response.status_code == 404


def test_same_current_and_target_is_400():
    response = client.get("/api/career/gap-analysis?current_title_id=7&target_title_id=7")
    assert response.status_code == 400


def test_gap_analysis_returns_readiness_and_radar():
    response = client.get(
        f"/api/career/gap-analysis?current_title_id={ACCOUNTANT}&target_title_id={FINANCE_MANAGER}"
    )
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["readiness_score"] <= 100
    assert body["level_source"] == "current_title_market_proxy"
    assert 3 <= len(body["radar"]) <= 8
    assert body["gap"]["evidence_postings"] == 16


def test_employee_levels_drive_the_split():
    repo = get_repository()
    top = service.analyze_gap(repo, ACCOUNTANT, FINANCE_MANAGER).radar[0].skill_id
    full = service.analyze_gap(repo, ACCOUNTANT, FINANCE_MANAGER, employee_skills={top: 5})
    assert full.level_source == "employee_profile"
    assert top in {s.skill_id for s in full.gap.matched}
    empty = service.analyze_gap(repo, ACCOUNTANT, FINANCE_MANAGER, employee_skills={})
    assert empty.readiness_score == 0
    assert top in {s.skill_id for s in empty.gap.missing}


def test_match_title_finds_the_profile_job_title():
    response = client.get("/api/career/titles/match", params={"job_title": "محاسب"})
    assert response.status_code == 200
    assert response.json()["id"] == ACCOUNTANT


def test_match_title_accepts_feminine_form_and_spelling_variants():
    for job_title in ["محاسبة", "مُحاسِبة", "مديرة مالية", "مطورة برمجيات", "Accountant"]:
        response = client.get("/api/career/titles/match", params={"job_title": job_title})
        assert response.status_code == 200, job_title
    assert (
        client.get("/api/career/titles/match", params={"job_title": "مطوّرة برمجيات"}).json()["id"]
        == 1
    )


def test_match_title_unknown_is_404():
    response = client.get("/api/career/titles/match", params={"job_title": "مسؤول سلامة"})
    assert response.status_code == 404


def test_feminine_senior_matches_the_masculine_title_words():
    assert service._title_words("محللة بيانات أولى") == service._title_words("محلل بيانات أول")


DATA_ANALYST, SENIOR_DATA_ANALYST = 11, 12


def test_noura_matches_the_data_analyst_ladder():
    for job_title, title_id in [("محللة بيانات", DATA_ANALYST), ("محللة بيانات أولى", 12)]:
        response = client.get("/api/career/titles/match", params={"job_title": job_title})
        assert response.json()["id"] == title_id
        assert response.json()["code"].startswith("DA-")
    assert response.json()["id"] == SENIOR_DATA_ANALYST


def test_gap_on_few_postings_is_flagged_as_low_evidence():
    thin = client.get(
        "/api/career/gap-analysis",
        params={"current_title_id": DATA_ANALYST, "target_title_id": SENIOR_DATA_ANALYST},
    ).json()
    assert thin["gap"]["evidence_postings"] < service.MIN_EVIDENCE_POSTINGS
    assert thin["gap"]["low_evidence"] is True
    solid = service.analyze_gap(get_repository(), ACCOUNTANT, FINANCE_MANAGER)
    assert solid.gap.low_evidence is False
