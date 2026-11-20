import json

import pytest
from fastapi.testclient import TestClient

from app.ai import llm
from app.main import app
from app.modules.onboarding import quiz, service

client = TestClient(app)

# Two questions quoted from data/company/documents/infosec.md, and one with an invented quote.
FAKE_MODEL_REPLY = json.dumps(
    {
        "questions": [
            {
                "question": "وش تسوي برموز التحقق؟",
                "options": ["أرسلها لزميلي", "لا أرسلها لأحد", "أحفظها في ملف", "أنشرها"],
                "answer": 1,
                "section_title": "## قواعد عامة",
                "quote": "لا ترسل رموز التحقق لأحد.",
            },
            {
                "question": "أي حساب تستخدم؟",
                "options": ["الحساب المؤسسي", "حسابي الشخصي"],
                "answer": 0,
                "section_title": "قواعد عامة",
                "quote": "استخدم الحساب المؤسسي فقط.",
            },
            {
                "question": "سؤال مخترع",
                "options": ["أ", "ب"],
                "answer": 0,
                "section_title": "قواعد عامة",
                "quote": "جملة ما هي موجودة في الوثيقة",
            },
        ]
    },
    ensure_ascii=False,
)


@pytest.fixture(autouse=True)
def fake_model(monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda system, user: FAKE_MODEL_REPLY)
    yield
    quiz.clear_quizzes()
    service.clear_quiz_scores()


def test_quiz_keeps_only_questions_quoted_from_the_document():
    body = client.get("/api/onboarding/lessons/infosec/quiz").json()

    assert body["topic"] == "أمن المعلومات"
    assert len(body["questions"]) == 2
    assert body["questions"][0]["source"]["section_title"] == "قواعد عامة"
    assert "answer" not in body["questions"][0]


def test_passing_the_quiz_takes_the_lesson_off_the_roadmap():
    lessons = [i for w in service.build_roadmap("emp-004").weeks for i in w.items]
    assert "أمن المعلومات" in {i.topic for i in lessons}

    client.get("/api/onboarding/lessons/infosec/quiz")
    result = client.post("/api/onboarding/lessons/infosec/attempt", json={"answers": [1, 0]}).json()

    assert result["score"] == 100 and result["passed"]
    lessons = [i for w in service.build_roadmap("emp-004").weeks for i in w.items]
    assert "أمن المعلومات" not in {i.topic for i in lessons}


def test_a_failed_retake_updates_the_score():
    client.get("/api/onboarding/lessons/infosec/quiz")
    result = client.post("/api/onboarding/lessons/infosec/attempt", json={"answers": [0, 0]}).json()

    assert result["score"] == 50 and not result["passed"]
    assert result["correct"] == [False, True]
    lesson = next(
        i
        for w in service.build_roadmap("emp-004").weeks
        for i in w.items
        if i.topic == "أمن المعلومات"
    )
    assert lesson.score == 50


def test_lessons_point_to_their_policy_document():
    lessons = [
        i for w in service.build_roadmap("emp-004").weeks for i in w.items if i.kind == "lesson"
    ]

    assert {i.document_id for i in lessons} == {
        "attendance",
        "infosec",
        "business-travel",
        "reimbursements",
    }


def test_quiz_errors():
    assert client.get("/api/onboarding/lessons/unknown/quiz").status_code == 404
    assert (
        client.post("/api/onboarding/lessons/infosec/attempt", json={"answers": [0]}).status_code
        == 404
    )
    client.get("/api/onboarding/lessons/infosec/quiz")
    assert (
        client.post("/api/onboarding/lessons/infosec/attempt", json={"answers": [0]}).status_code
        == 422
    )


def test_quiz_is_unavailable_without_the_model(monkeypatch):
    def not_configured(system, user):
        raise llm.LLMNotConfiguredError("no key")

    monkeypatch.setattr(llm, "generate", not_configured)
    assert client.get("/api/onboarding/lessons/attendance/quiz").status_code == 503
