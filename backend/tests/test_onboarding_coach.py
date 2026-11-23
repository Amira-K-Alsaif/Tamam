import json

import pytest
from fastapi.testclient import TestClient

from app.ai import llm
from app.main import app
from app.modules.onboarding import prompts, skill_profile, specialization

client = TestClient(app)
NOURA = "emp-004"


@pytest.fixture
def skill():
    return specialization.title_skills("محللة بيانات")[0]


def conversation(answers: int) -> list[dict]:
    messages = [{"role": "coach", "text": "سؤال أول"}]
    for n in range(answers):
        messages += [{"role": "employee", "text": f"جوابي {n}"}, {"role": "coach", "text": "تمام"}]
    return messages[:-1] if answers else messages


def fake_model(monkeypatch, text="فكرة وسؤال", level=None, raw=None):
    seen = []

    def reply(system, user, fast=False):
        seen.append((system, user, fast))
        return (
            raw
            if raw is not None
            else json.dumps({"text": text, "level": level}, ensure_ascii=False)
        )

    monkeypatch.setattr(llm, "generate", reply)
    return seen


def ask(skill_id: int, messages: list[dict]) -> dict:
    response = client.post(
        f"/api/onboarding/skills/{skill_id}/coach?employee_id={NOURA}", json={"messages": messages}
    )
    assert response.status_code == 200
    return response.json()


def test_the_coach_opens_at_the_employees_level_with_the_fast_model(monkeypatch, skill):
    seen = fake_model(monkeypatch)
    skill_profile.save(NOURA, {skill.id: 2})

    body = ask(skill.id, [])

    assert body == {"text": "فكرة وسؤال", "level_change": None}
    system, user, fast = seen[0]
    assert system == prompts.COACH_SYSTEM and fast
    assert f"<skill>{skill.label_ar}</skill>" in user and "<level>2</level>" in user
    assert "<can_update>no</can_update>" in user


def test_the_conversation_is_sent_back_to_the_coach(monkeypatch, skill):
    seen = fake_model(monkeypatch)

    ask(skill.id, conversation(1))

    assert "الموظف: جوابي 0" in seen[0][1]
    assert "تمّام: سؤال أول" in seen[0][1]


def test_the_coach_raises_the_level_one_step_once_enough_answers_show_it(monkeypatch, skill):
    seen = fake_model(monkeypatch, text="مستواك تحسّن!", level=4)
    skill_profile.save(NOURA, {skill.id: 1})

    body = ask(skill.id, conversation(3))

    assert "<can_update>yes</can_update>" in seen[0][1]
    assert body["text"] == "مستواك تحسّن!"
    change = body["level_change"]
    assert (change["previous_level"], change["level"]) == (1, 2)
    assert change["needed_level"] == specialization.expected_levels("محللة بيانات")[skill.id]
    assert skill_profile.levels(NOURA) == {skill.id: 2}


def test_the_level_does_not_change_before_enough_answers(monkeypatch, skill):
    fake_model(monkeypatch, level=4)
    skill_profile.save(NOURA, {skill.id: 1})

    body = ask(skill.id, conversation(2))

    assert body["level_change"] is None
    assert skill_profile.levels(NOURA) == {skill.id: 1}


def test_weak_answers_lower_the_level_one_step_at_most(monkeypatch, skill):
    fake_model(monkeypatch, level=0)
    skill_profile.save(NOURA, {skill.id: 3})

    body = ask(skill.id, conversation(3))

    assert body["level_change"]["level"] == 2


def test_no_judgement_or_the_same_level_changes_nothing(monkeypatch, skill):
    skill_profile.save(NOURA, {skill.id: 2})
    for level in (None, 2):
        fake_model(monkeypatch, level=level)
        assert ask(skill.id, conversation(4))["level_change"] is None
    assert skill_profile.levels(NOURA) == {skill.id: 2}


def test_a_reply_that_is_not_json_is_shown_but_changes_no_level(monkeypatch, skill):
    fake_model(monkeypatch, raw="رد عادي بدون تقييم")
    skill_profile.save(NOURA, {skill.id: 1})

    body = ask(skill.id, conversation(3))

    assert body == {"text": "رد عادي بدون تقييم", "level_change": None}
    assert skill_profile.levels(NOURA) == {skill.id: 1}


def test_only_the_employees_own_skills_can_be_coached(monkeypatch):
    fake_model(monkeypatch)
    title_skills = {s.id for s in specialization.title_skills("محللة بيانات")}
    other = next(s for s in specialization.dictionary().values() if s.id not in title_skills)

    response = client.post(
        f"/api/onboarding/skills/{other.id}/coach?employee_id={NOURA}", json={"messages": []}
    )

    assert response.status_code == 404


def test_the_coach_is_unavailable_without_the_model(monkeypatch, skill):
    def unavailable(system, user, **_):
        raise llm.LLMUnavailableError("busy")

    monkeypatch.setattr(llm, "generate", unavailable)

    response = client.post(
        f"/api/onboarding/skills/{skill.id}/coach?employee_id={NOURA}", json={"messages": []}
    )

    assert response.status_code == 503
