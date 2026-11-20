import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.career import plan, repository, service
from app.modules.career.repository import get_repository

client = TestClient(app)
ACCOUNTANT, FINANCE_MANAGER = 7, 8
DATA_ANALYST, SENIOR_DATA_ANALYST = 11, 12


@pytest.fixture(autouse=True)
def json_data_only(monkeypatch):
    monkeypatch.setattr(repository, "get_supabase", lambda: None)
    get_repository.cache_clear()
    yield
    get_repository.cache_clear()


def _considered(current: int, target: int) -> list[int]:
    gap = service.analyze_gap(get_repository(), current, target).gap
    return [s.skill_id for s in [*gap.matched, *gap.missing, *gap.to_improve]]


def _plan(current: int, target: int, employee_skills=None):
    repo = get_repository()
    gap = service.analyze_gap(repo, current, target, employee_skills)
    return gap, plan.build_plan(repo, gap)


def test_plan_covers_the_gap_most_requested_missing_skill_first():
    gap, result = _plan(ACCOUNTANT, FINANCE_MANAGER)
    planned = [a.skill_id for p in result.phases for a in p.actions]
    gap_skills = {s.skill_id for s in [*gap.gap.missing, *gap.gap.to_improve]}
    assert set(planned) <= gap_skills
    top_missing = max(gap.gap.missing, key=lambda s: s.market_frequency)
    assert result.phases[0].actions[0].skill_id == top_missing.skill_id
    assert [p.phase for p in result.phases] == ["30", "60", "90"]
    assert all(len({a.skill_id for a in p.actions}) <= plan.SKILLS_PER_PHASE for p in result.phases)


def test_skills_already_held_are_not_in_the_plan():
    gap, result = _plan(ACCOUNTANT, FINANCE_MANAGER)
    held = {s.skill_id for s in gap.gap.matched}
    assert not held & {a.skill_id for p in result.phases for a in p.actions}


def test_a_skill_to_improve_gets_practice_not_an_introduction():
    skills = _considered(ACCOUNTANT, FINANCE_MANAGER)
    weak = skills[0]
    levels = {skill_id: 5 for skill_id in skills} | {weak: 1}
    _, result = _plan(ACCOUNTANT, FINANCE_MANAGER, levels)
    actions = [a for p in result.phases for a in p.actions if a.skill_id == weak]
    assert len(actions) == 1 and actions[0].effort_hours == plan.HOURS_TO_IMPROVE


def test_nothing_to_learn_gives_an_empty_plan():
    levels = {skill_id: 5 for skill_id in _considered(ACCOUNTANT, FINANCE_MANAGER)}
    _, result = _plan(ACCOUNTANT, FINANCE_MANAGER, levels)
    assert result.phases == [] and result.readiness_score == 100


def test_plan_endpoint_for_the_demo_employee_keeps_the_low_evidence_flag():
    response = client.get(
        "/api/career/plan",
        params={"current_title_id": DATA_ANALYST, "target_title_id": SENIOR_DATA_ANALYST},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["low_evidence"] is True
    assert body["phases"][0]["phase"] == "30"
    assert all(a["title_ar"] for a in body["phases"][0]["actions"])


def test_plan_endpoint_errors():
    same = client.get("/api/career/plan", params={"current_title_id": 7, "target_title_id": 7})
    assert same.status_code == 400
    unknown = client.get("/api/career/plan", params={"current_title_id": 999, "target_title_id": 8})
    assert unknown.status_code == 404
