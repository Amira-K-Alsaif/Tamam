import pytest

from app.modules.onboarding import mock_data, service

# Starting-assessment scores for the three demo new hires, as if each had taken the generated
# assessment. Roadmap tests need lessons to order; new hires have none until they take it.
NEW_HIRE_SCORES = {
    "emp-004": {
        "سياسة الإجازات": 80,
        "الحضور والانصراف": 65,
        "أمن المعلومات": 40,
        "السفر والانتداب": 30,
        "المصروفات والمطالبات": 55,
    },
    "emp-006": {
        "سياسة الإجازات": 90,
        "الحضور والانصراف": 85,
        "أمن المعلومات": 75,
        "السفر والانتداب": 60,
        "المصروفات والمطالبات": 80,
    },
    "emp-007": {
        "سياسة الإجازات": 50,
        "الحضور والانصراف": 45,
        "أمن المعلومات": 35,
        "السفر والانتداب": 20,
        "المصروفات والمطالبات": 40,
    },
}


@pytest.fixture
def new_hires_assessed():
    for employee_id, scores in NEW_HIRE_SCORES.items():
        service.record_scores(employee_id, scores, taken_at=mock_data.ASSESSMENT_TAKEN_AT)
    yield
    service.clear_quiz_scores()
