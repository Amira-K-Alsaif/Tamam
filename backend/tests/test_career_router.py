from fastapi.testclient import TestClient

from app.main import app
from app.modules.career import service
from app.modules.career.repository import get_repository

client = TestClient(app)
ACCOUNTANT, FINANCE_MANAGER = 7, 8


def test_titles_lists_the_ten_titles_with_their_next_step():
    titles = client.get("/api/career/titles").json()
    assert len(titles) == 10
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
