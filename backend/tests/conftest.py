from datetime import UTC, datetime

import pytest

from app.modules.onboarding import assessment, documents, roadmap_ai, service, skill_profile

# Policy scores for four employees, as if each had taken the starting assessment.
# Roadmap tests need lessons to order; nobody has any until they take it.
ASSESSED_AT = datetime(2026, 11, 2, 6, 0, tzinfo=UTC)
ASSESSED_SCORES = {
    "emp-003": {
        "سياسة الإجازات السنوية": 90,
        "سياسة الحضور وساعات العمل": 85,
        "سياسة أمن المعلومات": 88,
        "سياسة السفر لمهام العمل": 75,
        "إجراء تعويض مصاريف العمل": 80,
    },
    "emp-004": {
        "سياسة الإجازات السنوية": 80,
        "سياسة الحضور وساعات العمل": 65,
        "سياسة أمن المعلومات": 40,
        "سياسة السفر لمهام العمل": 30,
        "إجراء تعويض مصاريف العمل": 55,
    },
    "emp-006": {
        "سياسة الإجازات السنوية": 90,
        "سياسة الحضور وساعات العمل": 85,
        "سياسة أمن المعلومات": 75,
        "سياسة السفر لمهام العمل": 60,
        "إجراء تعويض مصاريف العمل": 80,
    },
    "emp-007": {
        "سياسة الإجازات السنوية": 50,
        "سياسة الحضور وساعات العمل": 45,
        "سياسة أمن المعلومات": 35,
        "سياسة السفر لمهام العمل": 20,
        "إجراء تعويض مصاريف العمل": 40,
    },
}


@pytest.fixture
def employees_assessed():
    for employee_id, scores in ASSESSED_SCORES.items():
        service.record_scores(employee_id, scores, taken_at=ASSESSED_AT)
    yield
    service.clear_quiz_scores()


@pytest.fixture(autouse=True)
def fresh_onboarding_state(monkeypatch):
    """Every test starts with no assessment, skill profile, plan, or score recorded, and no
    saved question bank, so questions come from the (faked) model unless a test adds a bank."""
    monkeypatch.setattr(documents, "bank", lambda: {})
    yield
    assessment.clear_assessment()
    roadmap_ai.clear()
    skill_profile.clear()
    service.clear_quiz_scores()
