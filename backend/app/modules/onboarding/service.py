"""Builds the onboarding roadmap: knowledge gaps, missing access, and people to meet."""

from . import mock_data
from .schemas import (
    AccessStatus,
    AssessmentResult,
    EmployeeProfile,
    Roadmap,
    RoadmapItem,
    RoadmapWeek,
)

# A topic scored below this becomes a lesson on the roadmap.
PASSING_SCORE = 70
# How many lessons go in each week, lowest scores first.
LESSONS_PER_WEEK = 2
# The approver_role value that means "the employee's own manager".
DIRECT_MANAGER_ROLE = "المدير المباشر"

STATUS_LABELS: dict[AccessStatus, str] = {
    "active": "مفعّلة",
    "requested": "تم الطلب، بانتظار الموافقة",
    "missing": "ناقصة، تحتاج طلب",
}


def get_employee(employee_id: str) -> EmployeeProfile:
    for employee in mock_data.EMPLOYEES:
        if employee.id == employee_id:
            return employee
    raise LookupError(f"Unknown employee: {employee_id}")


def latest_scores(results: list[AssessmentResult]) -> dict[str, int]:
    """Keep only the newest score per topic, so a retaken quiz replaces the old one."""
    newest: dict[str, AssessmentResult] = {}
    for result in results:
        current = newest.get(result.topic)
        if current is None or result.taken_at > current.taken_at:
            newest[result.topic] = result
    return {topic: result.score for topic, result in newest.items()}


def knowledge_gaps(employee_id: str) -> list[RoadmapItem]:
    results = [r for r in mock_data.ASSESSMENT_RESULTS if r.employee_id == employee_id]
    scores = latest_scores(results)
    weak = sorted(
        ((topic, score) for topic, score in scores.items() if score < PASSING_SCORE),
        key=lambda pair: pair[1],
    )
    return [
        RoadmapItem(
            kind="lesson",
            title=f"درس: {topic}",
            reason=f"درجتك في التقييم {score} من 100، والمطلوب {PASSING_SCORE}.",
            week=index // LESSONS_PER_WEEK + 1,
            score=score,
        )
        for index, (topic, score) in enumerate(weak)
    ]


def missing_access(employee: EmployeeProfile) -> list[RoadmapItem]:
    statuses = {
        row.access_item_id: row.status
        for row in mock_data.EMPLOYEE_ACCESS
        if row.employee_id == employee.id
    }
    items: list[RoadmapItem] = []
    for access in mock_data.ACCESS_ITEMS:
        if employee.job_title not in access.required_for_job_titles:
            continue
        status = statuses.get(access.id, "missing")
        if status == "active":
            continue
        items.append(
            RoadmapItem(
                kind="access",
                title=access.system_name,
                reason=f"مطلوبة لمسمى {employee.job_title}. الحالة: {STATUS_LABELS[status]}.",
                week=1,
                access_item_id=access.id,
                status=status,
                procedure_id=access.procedure_id,
                approver_role=access.approver_role,
                expected_days=access.expected_days,
            )
        )
    return items


def people_to_meet(employee: EmployeeProfile, access_items: list[RoadmapItem]) -> list[RoadmapItem]:
    """The manager, plus whoever approves the access the employee is still missing."""
    reasons: dict[str, list[str]] = {}
    if employee.manager_id:
        reasons[employee.manager_id] = ["المدير المباشر"]

    for item in access_items:
        if item.approver_role == DIRECT_MANAGER_ROLE:
            approver_id = employee.manager_id
        else:
            approver_id = next(
                (e.id for e in mock_data.EMPLOYEES if e.job_title == item.approver_role),
                None,
            )
        if approver_id is None or approver_id == employee.id:
            continue
        reasons.setdefault(approver_id, []).append(f"يوافق على {item.title}")

    people: list[RoadmapItem] = []
    for person_id, person_reasons in reasons.items():
        person = get_employee(person_id)
        people.append(
            RoadmapItem(
                kind="person",
                title=f"{person.full_name} · {person.job_title}",
                reason="، ".join(person_reasons),
                week=1,
                employee_id=person.id,
            )
        )
    return people


def build_roadmap(employee_id: str) -> Roadmap:
    employee = get_employee(employee_id)
    access = missing_access(employee)
    items = access + people_to_meet(employee, access) + knowledge_gaps(employee_id)

    weeks: dict[int, list[RoadmapItem]] = {}
    for item in items:
        weeks.setdefault(item.week, []).append(item)
    return Roadmap(
        employee_id=employee_id,
        weeks=[RoadmapWeek(week=week, items=weeks[week]) for week in sorted(weeks)],
    )
