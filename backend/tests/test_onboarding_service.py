from datetime import UTC, datetime

import pytest

from app.modules.onboarding.mock_data import CURRENT_EMPLOYEE_ID
from app.modules.onboarding.schemas import AssessmentResult
from app.modules.onboarding.service import (
    PASSING_SCORE,
    build_roadmap,
    get_current_employee,
    get_employee,
    knowledge_gaps,
    latest_scores,
    missing_access,
    people_to_meet,
)

pytestmark = pytest.mark.usefixtures("new_hires_assessed")


def test_retaken_quiz_replaces_the_old_score():
    old = AssessmentResult(
        employee_id="e", topic="t", score=30, taken_at=datetime(2026, 11, 1, tzinfo=UTC)
    )
    new = AssessmentResult(
        employee_id="e", topic="t", score=90, taken_at=datetime(2026, 11, 5, tzinfo=UTC)
    )
    assert latest_scores([new, old]) == {"t": 90}


def test_only_weak_topics_become_lessons_lowest_first():
    lessons = knowledge_gaps(CURRENT_EMPLOYEE_ID)
    scores = [item.score for item in lessons]

    assert all(score < PASSING_SCORE for score in scores)
    assert scores == sorted(scores)
    assert [item.week for item in lessons] == [1, 1, 2, 2]


def test_active_access_is_left_out():
    employee = get_employee(CURRENT_EMPLOYEE_ID)
    access = missing_access(employee)

    assert {item.access_item_id for item in access} == {"acc-vpn", "acc-dwh", "acc-bi"}
    assert all(item.status != "active" for item in access)


def test_people_are_the_manager_and_the_approvers_once_each():
    employee = get_employee(CURRENT_EMPLOYEE_ID)
    people = people_to_meet(employee, missing_access(employee))
    ids = [item.employee_id for item in people]

    assert ids == ["emp-002", "emp-005"]
    assert employee.id not in ids


def test_roadmap_is_grouped_by_week_in_order():
    roadmap = build_roadmap(CURRENT_EMPLOYEE_ID)

    assert [week.week for week in roadmap.weeks] == [1, 2]
    assert all(item.week == week.week for week in roadmap.weeks for item in week.items)


def test_unknown_employee_raises():
    with pytest.raises(LookupError):
        build_roadmap("emp-999")


def test_current_employee_names_the_direct_manager():
    assert get_current_employee("emp-004").manager_name == "سارة القحطاني"


def test_the_ceo_has_no_manager_name():
    assert get_current_employee("emp-001").manager_name is None
