import json

import pytest
from fastapi.testclient import TestClient

from app.ai import llm
from app.main import app
from app.modules.onboarding import assessment, documents, quiz, service, skill_profile
from app.modules.onboarding import specialization as spec

client = TestClient(app)
NOURA = "emp-004"  # محللة بيانات in البيانات والتحليلات: her title's skills are in the career data


def saved_question(doc_id: str, number: int) -> dict:
    title, markdown = documents.load_document(doc_id)
    sentence = next(
        line.strip()
        for line in markdown.splitlines()
        if line.strip() and not line.startswith(("#", "-", "|"))
    )
    return {
        "question": f"سؤال {number} عن {title}",
        "options": ["صح", "خطأ"],
        "answer": 0,
        "source": {
            "document_id": doc_id,
            "document_title": title,
            "page": None,
            "section_title": "قسم",
            "quote": sentence,
        },
    }


@pytest.fixture
def bank(monkeypatch):
    """Five saved questions for every policy, as build_questions.py writes them."""
    saved = {
        doc_id: [saved_question(doc_id, n) for n in range(5)] for doc_id, _ in documents.policies()
    }
    monkeypatch.setattr(documents, "bank", lambda: saved)
    return saved


def drawn_plan(user: str) -> str:
    gaps = json.loads(user.split("<gaps>\n")[1].split("\n</gaps>")[0])
    items = [
        {"kind": gap["kind"], "id": gap["id"], "week": 1, "reason": f"خطة تمّام لـ {gap['title']}"}
        for gap in gaps
    ]
    items.append({"kind": "lesson", "id": "invented", "week": 1, "reason": "عنصر مخترع"})
    return json.dumps({"items": items}, ensure_ascii=False)


@pytest.fixture
def model(monkeypatch):
    """The model only draws the roadmap; it records whether it was asked for a fast reply."""
    calls = []

    def reply(system, user, fast=False):
        calls.append(fast)
        return drawn_plan(user)

    monkeypatch.setattr(llm, "generate", reply)
    return calls


def take_assessment(employee_id: str, wrong_policy: str | None = None, level: int = 4) -> dict:
    questions = client.get(f"/api/onboarding/assessment?employee_id={employee_id}").json()
    answers = [
        level if q["kind"] == "skill" else (1 if q["topic"] == wrong_policy else 0)
        for q in questions["questions"]
    ]
    return client.post(
        f"/api/onboarding/assessment/attempt?employee_id={employee_id}", json={"answers": answers}
    ).json()


def roadmap_items(employee_id: str, kind: str) -> list:
    roadmap = service.build_roadmap(employee_id)
    return [item for week in roadmap.weeks for item in week.items if item.kind == kind]


def test_every_employee_starts_with_the_assessment():
    for employee_id in ["emp-004", "emp-002"]:
        roadmap = service.build_roadmap(employee_id)
        assert not roadmap.assessed
        assert not roadmap_items(employee_id, "lesson") and not roadmap_items(employee_id, "skill")
    team = {member.employee.id: member for member in service.build_team("emp-002")}
    assert team[NOURA].next_step == service.STARTING_ASSESSMENT


def test_the_assessment_opens_from_the_bank_without_the_model(bank, monkeypatch):
    def must_not_call(system, user, **_):
        raise AssertionError("the assessment must not wait on the model")

    monkeypatch.setattr(llm, "generate", must_not_call)

    body = client.get(f"/api/onboarding/assessment?employee_id={NOURA}").json()

    company = [q for q in body["questions"] if q["kind"] == "company"]
    skills = [q for q in body["questions"] if q["kind"] == "skill"]
    assert [q["source"]["document_id"] for q in company[::2]] == documents.policies_for(
        "البيانات والتحليلات", assessment.COMPANY_POLICIES
    )
    assert len(company) == 2 * assessment.COMPANY_POLICIES
    assert [q["skill_id"] for q in skills] == [s.id for s in spec.title_skills("محللة بيانات")]
    assert skills[0]["options"] == assessment.LEVELS
    assert all(q["source"] is None for q in skills)
    assert "answer" not in body["questions"][0]


def test_policies_start_with_the_employees_own_department():
    picked = documents.policies_for("البيانات والتحليلات", 3)

    assert picked[:2] == ["classification", "dashboards"]
    assert picked[2] == documents.COMPANY_WIDE[0]
    assert documents.policies_for("قسم غير موجود", 2) == documents.COMPANY_WIDE[:2]


def test_answers_become_policy_scores_skill_levels_and_an_ai_roadmap(bank, model):
    outcome = take_assessment(NOURA, wrong_policy="سياسة تصنيف البيانات", level=1)

    scores = {topic["document_id"]: topic["score"] for topic in outcome["topics"]}
    assert scores["classification"] == 0 and scores["dashboards"] == 100
    title_skills = spec.title_skills("محللة بيانات")
    assert skill_profile.levels(NOURA) == {skill.id: 1 for skill in title_skills}
    assert all(result["level"] == 1 for result in outcome["skills"])
    assert outcome["correct"][-1] is None and outcome["correct_options"][-1] is None

    roadmap = service.build_roadmap(NOURA)
    assert roadmap.assessed and roadmap.drawn_by == "ai"
    assert [lesson.document_id for lesson in roadmap_items(NOURA, "lesson")] == ["classification"]
    skills = roadmap_items(NOURA, "skill")
    assert {skill.skill_id for skill in skills} == {s.id for s in title_skills}
    assert skills[0].reason.startswith("خطة تمّام لـ ")
    assert model == [True]


def test_skills_at_the_needed_level_are_not_gaps(bank, model):
    take_assessment(NOURA, level=4)

    assert roadmap_items(NOURA, "skill") == []
    assert service.build_progress(NOURA).skills_ready == len(spec.title_skills("محللة بيانات"))


def test_without_a_drawn_plan_every_gap_is_still_on_the_roadmap(bank, monkeypatch):
    def unavailable(system, user, **_):
        raise llm.LLMUnavailableError("busy")

    monkeypatch.setattr(llm, "generate", unavailable)

    take_assessment(NOURA, wrong_policy="سياسة تصنيف البيانات", level=0)

    roadmap = service.build_roadmap(NOURA)
    assert roadmap.drawn_by == "rules"
    assert [lesson.document_id for lesson in roadmap_items(NOURA, "lesson")] == ["classification"]
    assert len(roadmap_items(NOURA, "skill")) == len(spec.title_skills("محللة بيانات"))


def test_scores_and_levels_belong_only_to_the_employee_who_answered(bank, model):
    take_assessment(NOURA, level=0)

    assert service.has_assessment(NOURA)
    assert not service.has_assessment("emp-006")
    assert skill_profile.levels("emp-006") is None


def test_the_lesson_quiz_uses_the_saved_questions_the_assessment_did_not_ask(bank):
    lesson = client.get("/api/onboarding/lessons/classification/quiz").json()
    asked = client.get(f"/api/onboarding/assessment?employee_id={NOURA}").json()["questions"]

    lesson_questions = {q["question"] for q in lesson["questions"]}
    assert len(lesson_questions) == 5 - quiz.ASSESSMENT_QUESTIONS
    assert not lesson_questions & {q["question"] for q in asked}


def test_a_level_outside_the_options_is_rejected(bank):
    questions = client.get(f"/api/onboarding/assessment?employee_id={NOURA}").json()["questions"]
    answers = [9 if q["kind"] == "skill" else 0 for q in questions]

    response = client.post(
        f"/api/onboarding/assessment/attempt?employee_id={NOURA}", json={"answers": answers}
    )

    assert response.status_code == 422


def test_the_assessment_is_unavailable_without_bank_or_model(monkeypatch):
    def not_configured(system, user, **_):
        raise llm.LLMNotConfiguredError("no key")

    monkeypatch.setattr(llm, "generate", not_configured)

    body = client.get(f"/api/onboarding/assessment?employee_id={NOURA}").json()
    assert {q["kind"] for q in body["questions"]} == {"skill"}
    # A manager's title has no skill data, so with no policy questions there is nothing to ask.
    assert client.get("/api/onboarding/assessment?employee_id=emp-002").status_code == 503


def test_answering_errors(bank):
    attempt = f"/api/onboarding/assessment/attempt?employee_id={NOURA}"
    assert client.post(attempt, json={"answers": [0]}).status_code == 404

    client.get(f"/api/onboarding/assessment?employee_id={NOURA}")
    assert client.post(attempt, json={"answers": [0]}).status_code == 422
