import json

import pytest
from fastapi.testclient import TestClient

from app.ai import llm
from app.main import app
from app.modules.career import plan, plan_ai, repository, service
from app.modules.career.repository import get_repository


@pytest.fixture(autouse=True)
def no_plan_model(monkeypatch):
    """Normal tests never call the real model: the plan route falls back to the rule plan."""

    def not_configured(system, user, **_):
        raise llm.LLMNotConfiguredError("no key in tests")

    monkeypatch.setattr(llm, "generate", not_configured)
    plan_ai.clear()
    yield
    plan_ai.clear()


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


def _fake_plan(monkeypatch, gap, extra_actions=()):
    target = [*gap.gap.missing, *gap.gap.to_improve][0]
    reply = {
        "phases": [
            {
                "phase": "30",
                "goal_ar": "ابني الأساس",
                "actions": [
                    {
                        "skill_id": target.skill_id,
                        "type": "practice",
                        "title_ar": "حللي تقرير المصروفات الشهري بنفسك",
                        "steps_ar": ["اختاري شهر", "قارني بالموازنة", ""],
                        "success_metric_ar": "جدول مقارنة مكتمل",
                        "effort_hours": 6,
                    },
                    *extra_actions,
                ],
            },
            {"phase": "60", "goal_ar": "مرحلة بلا خطوات صالحة", "actions": []},
        ]
    }
    calls = []

    def fake(system, user, fast=False):
        calls.append(fast)
        return json.dumps(reply, ensure_ascii=False)

    monkeypatch.setattr(llm, "generate", fake)
    return target, calls


def test_the_model_writes_a_self_directed_plan_from_the_real_gap(monkeypatch):
    repo = get_repository()
    gap = service.analyze_gap(repo, ACCOUNTANT, FINANCE_MANAGER)
    invented = {
        "skill_id": 99999,
        "type": "practice",
        "title_ar": "مهارة مو في الفجوة",
        "steps_ar": [],
        "success_metric_ar": "-",
        "effort_hours": 2,
    }
    wrong_type = {**invented, "skill_id": gap.gap.missing[0].skill_id, "type": "mentoring"}
    target, calls = _fake_plan(monkeypatch, gap, extra_actions=(invented, wrong_type))

    result = plan_ai.write_plan(repo, gap)

    assert result.written_by == "ai" and calls == [True]
    assert [p.phase for p in result.phases] == ["30"]
    (action,) = result.phases[0].actions
    assert action.skill_id == target.skill_id
    assert action.steps_ar == ["اختاري شهر", "قارني بالموازنة"]


def test_the_plan_endpoint_uses_the_written_plan_and_falls_back_to_rules(monkeypatch):
    params = {"current_title_id": ACCOUNTANT, "target_title_id": FINANCE_MANAGER}
    assert client.get("/api/career/plan", params=params).json()["written_by"] == "rules"

    gap = service.analyze_gap(get_repository(), ACCOUNTANT, FINANCE_MANAGER)
    _fake_plan(monkeypatch, gap)
    assert client.get("/api/career/plan", params=params).json()["written_by"] == "ai"


def test_an_unusable_plan_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda system, user, **_: "خطة بدون JSON")

    body = client.get(
        "/api/career/plan",
        params={"current_title_id": ACCOUNTANT, "target_title_id": FINANCE_MANAGER},
    ).json()

    assert body["written_by"] == "rules" and body["phases"]


def test_rule_actions_need_no_one_elses_time():
    _, result = _plan(ACCOUNTANT, FINANCE_MANAGER)
    actions = [a for p in result.phases for a in p.actions]

    assert {a.type for a in actions} <= {"self_study", "practice", "project", "certification"}
    assert all(a.steps_ar for a in actions)
    assert not any("مدير" in a.title_ar or "زميل" in a.title_ar for a in actions)
