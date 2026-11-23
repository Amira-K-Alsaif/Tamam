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
    return messages


def fake_model(monkeypatch, coach_text="فكرة وسؤال", judged_level=4):
    seen = []

    def reply(system, user, fast=False):
        seen.append((system, user, fast))
        if system == prompts.LEVEL_CHECK_SYSTEM:
            return json.dumps(
                {"level": judged_level, "reason": "أثبتي الأساسيات."}, ensure_ascii=False
            )
        return coach_text

    monkeypatch.setattr(llm, "generate", reply)
    return seen


def test_the_coach_opens_at_the_employees_level_with_the_fast_model(monkeypatch, skill):
    seen = fake_model(monkeypatch)
    skill_profile.save(NOURA, {skill.id: 2})

    body = client.post(
        f"/api/onboarding/skills/{skill.id}/coach?employee_id={NOURA}", json={"messages": []}
    ).json()

    assert body == {"text": "فكرة وسؤال"}
    system, user, fast = seen[0]
    assert system == prompts.COACH_SYSTEM and fast
    assert f"<skill>{skill.label_ar}</skill>" in user and "<level>2</level>" in user


def test_the_conversation_is_sent_back_to_the_coach(monkeypatch, skill):
    seen = fake_model(monkeypatch)

    client.post(
        f"/api/onboarding/skills/{skill.id}/coach?employee_id={NOURA}",
        json={"messages": conversation(1)},
    )

    assert "الموظف: جوابي 0" in seen[0][1]
    assert "تمّام: سؤال أول" in seen[0][1]


def test_the_level_moves_one_step_toward_the_judgement(monkeypatch, skill):
    fake_model(monkeypatch, judged_level=4)
    skill_profile.save(NOURA, {skill.id: 1})

    body = client.post(
        f"/api/onboarding/skills/{skill.id}/level-check?employee_id={NOURA}",
        json={"messages": conversation(3)},
    ).json()

    assert (body["previous_level"], body["level"]) == (1, 2)
    assert body["reason"] == "أثبتي الأساسيات."
    assert skill_profile.levels(NOURA) == {skill.id: 2}


def test_a_weak_conversation_lowers_the_level_one_step_at_most(monkeypatch, skill):
    fake_model(monkeypatch, judged_level=0)
    skill_profile.save(NOURA, {skill.id: 3})

    body = client.post(
        f"/api/onboarding/skills/{skill.id}/level-check?employee_id={NOURA}",
        json={"messages": conversation(3)},
    ).json()

    assert body["level"] == 2


def test_the_level_needs_a_few_answers_first(monkeypatch, skill):
    fake_model(monkeypatch)

    response = client.post(
        f"/api/onboarding/skills/{skill.id}/level-check?employee_id={NOURA}",
        json={"messages": conversation(2)},
    )

    assert response.status_code == 422
    assert skill_profile.levels(NOURA) is None


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


def test_an_unusable_judgement_changes_nothing(monkeypatch, skill):
    monkeypatch.setattr(llm, "generate", lambda system, user, **_: "مستواك ممتاز")
    skill_profile.save(NOURA, {skill.id: 1})

    response = client.post(
        f"/api/onboarding/skills/{skill.id}/level-check?employee_id={NOURA}",
        json={"messages": conversation(3)},
    )

    assert response.status_code == 503
    assert skill_profile.levels(NOURA) == {skill.id: 1}
