import json
import re

import pytest
from fastapi.testclient import TestClient

from app.ai import llm
from app.main import app
from app.modules.onboarding import assessment, mock_data, quiz, service

client = TestClient(app)
NEW_HIRE = "emp-004"
TOPICS = list(mock_data.TOPIC_DOCUMENTS)


def quoting_model(skip_document_titles: tuple[str, ...] = ()):
    """A fake model that writes two questions, each quoting a real sentence of the document.

    The right answer is always option 0. Documents whose title is skipped get invented quotes,
    which the server must reject.
    """

    def reply(system, user):
        title = re.search(r'<document title="([^"]+)">', user).group(1)
        sentences = [
            line.strip()
            for line in user.splitlines()
            if line.strip() and not line.startswith(("#", "<", "-", "|"))
        ]
        questions = [
            {
                "question": f"سؤال {index} من {title}",
                "options": ["صح", "خطأ"],
                "answer": 0,
                "section_title": "قسم",
                "quote": "جملة مخترعة" if title in skip_document_titles else sentence,
            }
            for index, sentence in enumerate(sentences[:2])
        ]
        return json.dumps({"questions": questions}, ensure_ascii=False)

    return reply


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    monkeypatch.setattr(llm, "generate", quoting_model())
    yield
    assessment.clear_assessment()
    quiz.clear_quizzes()
    service.clear_quiz_scores()


def lessons(employee_id: str) -> set[str]:
    roadmap = service.build_roadmap(employee_id)
    return {item.topic for week in roadmap.weeks for item in week.items if item.kind == "lesson"}


def test_a_new_hire_starts_with_the_assessment_and_no_lessons():
    assert lessons(NEW_HIRE) == set()
    assert not service.has_assessment(NEW_HIRE)
    first_step = next(b for b in service.build_progress(NEW_HIRE).badges if b.id == "first-step")
    assert not first_step.earned
    team = {m.employee.id: m for m in service.build_team("emp-002")}
    assert team[NEW_HIRE].next_step == service.STARTING_ASSESSMENT


def test_the_assessment_asks_two_questions_per_topic_without_answers():
    body = client.get("/api/onboarding/assessment").json()

    topics = [question["topic"] for question in body["questions"]]
    assert {topic: topics.count(topic) for topic in TOPICS} == dict.fromkeys(TOPICS, 2)
    assert "answer" not in body["questions"][0]
    assert body["questions"][0]["source"]["document_id"] in mock_data.TOPIC_DOCUMENTS.values()


def test_weak_topics_from_the_assessment_become_lessons():
    questions = client.get("/api/onboarding/assessment").json()["questions"]
    weak = {"أمن المعلومات", "السفر والانتداب"}
    answers = [1 if question["topic"] in weak else 0 for question in questions]

    outcome = client.post(
        f"/api/onboarding/assessment/attempt?employee_id={NEW_HIRE}", json={"answers": answers}
    ).json()

    scores = {s["topic"]: (s["score"], s["passed"]) for s in outcome["scores"]}
    assert scores["أمن المعلومات"] == (0, False)
    assert scores["سياسة الإجازات"] == (100, True)
    assert lessons(NEW_HIRE) == weak
    assert service.has_assessment(NEW_HIRE)


def test_the_scores_belong_only_to_the_employee_who_answered():
    questions = client.get("/api/onboarding/assessment").json()["questions"]
    client.post(
        f"/api/onboarding/assessment/attempt?employee_id={NEW_HIRE}",
        json={"answers": [1] * len(questions)},
    )

    assert service.has_assessment(NEW_HIRE)
    assert not service.has_assessment("emp-006")


def test_a_topic_whose_questions_cannot_be_traced_is_left_out(monkeypatch):
    infosec_title = quiz.load_document("infosec")[0]
    monkeypatch.setattr(llm, "generate", quoting_model(skip_document_titles=(infosec_title,)))

    topics = {q["topic"] for q in client.get("/api/onboarding/assessment").json()["questions"]}

    assert "أمن المعلومات" not in topics
    assert len(topics) == len(TOPICS) - 1


def test_the_assessment_is_unavailable_without_the_model(monkeypatch):
    def not_configured(system, user):
        raise llm.LLMNotConfiguredError("no key")

    monkeypatch.setattr(llm, "generate", not_configured)

    assert client.get("/api/onboarding/assessment").status_code == 503


def test_answering_errors():
    attempt = f"/api/onboarding/assessment/attempt?employee_id={NEW_HIRE}"
    assert client.post(attempt, json={"answers": [0]}).status_code == 404

    client.get("/api/onboarding/assessment")
    assert client.post(attempt, json={"answers": [0]}).status_code == 422
