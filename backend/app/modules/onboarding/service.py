"""Builds the onboarding roadmap: knowledge gaps, missing access, and people to meet."""

from datetime import UTC, datetime

from . import mock_data
from .schemas import (
    AssessmentResult,
    Badge,
    CurrentEmployee,
    EmployeeProfile,
    Progress,
    Roadmap,
    RoadmapItem,
    RoadmapWeek,
    TeamMember,
)

# A topic scored below this becomes a lesson on the roadmap.
PASSING_SCORE = 70
# How many lessons go in each week, lowest scores first.
LESSONS_PER_WEEK = 2
# The approver_role value that means "the employee's own manager".
DIRECT_MANAGER_ROLE = "المدير المباشر"


def get_employee(employee_id: str) -> EmployeeProfile:
    for employee in mock_data.EMPLOYEES:
        if employee.id == employee_id:
            return employee
    raise LookupError(f"Unknown employee: {employee_id}")


def get_current_employee(employee_id: str) -> CurrentEmployee:
    """The employee with their manager's name, so forms can name the direct manager."""
    employee = get_employee(employee_id)
    manager_name = get_employee(employee.manager_id).full_name if employee.manager_id else None
    return CurrentEmployee(**employee.model_dump(), manager_name=manager_name)


# Quiz retakes during this run of the server. They join the starting assessment, and the newest
# score per topic counts, so the roadmap reorders as quizzes are retaken. Moves to Supabase later.
_retakes: list[AssessmentResult] = []


def assessment_results(employee_id: str) -> list[AssessmentResult]:
    every = [*mock_data.ASSESSMENT_RESULTS, *_retakes]
    return [result for result in every if result.employee_id == employee_id]


def record_quiz_score(employee_id: str, topic: str, score: int) -> None:
    get_employee(employee_id)
    _retakes.append(
        AssessmentResult(
            employee_id=employee_id, topic=topic, score=score, taken_at=datetime.now(UTC)
        )
    )


def clear_quiz_scores() -> None:
    """Forgets every retake; for tests and for restarting a demo."""
    _retakes.clear()


def latest_scores(results: list[AssessmentResult]) -> dict[str, int]:
    """Keep only the newest score per topic, so a retaken quiz replaces the old one."""
    newest: dict[str, AssessmentResult] = {}
    for result in results:
        current = newest.get(result.topic)
        if current is None or result.taken_at > current.taken_at:
            newest[result.topic] = result
    return {topic: result.score for topic, result in newest.items()}


def knowledge_gaps(employee_id: str) -> list[RoadmapItem]:
    scores = latest_scores(assessment_results(employee_id))
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
            topic=topic,
            document_id=mock_data.TOPIC_DOCUMENTS.get(topic),
        )
        for index, (topic, score) in enumerate(weak)
    ]


def missing_access(employee: EmployeeProfile) -> list[RoadmapItem]:
    statuses = access_statuses(employee)
    items: list[RoadmapItem] = []
    for access in mock_data.ACCESS_ITEMS:
        status = statuses.get(access.id)
        if status is None or status == "active":
            continue
        items.append(
            RoadmapItem(
                kind="access",
                title=access.system_name,
                reason=f"مطلوبة لمسمى {employee.job_title}.",
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


def access_statuses(employee: EmployeeProfile) -> dict[str, str]:
    """Status of every access item the employee's job title needs; no row means missing."""
    rows = {
        row.access_item_id: row.status
        for row in mock_data.EMPLOYEE_ACCESS
        if row.employee_id == employee.id
    }
    return {
        item.id: rows.get(item.id, "missing")
        for item in mock_data.ACCESS_ITEMS
        if employee.job_title in item.required_for_job_titles
    }


def build_badges(
    has_assessment: bool, access_done: bool, topics_done: bool, percent: int
) -> list[Badge]:
    return [
        Badge(
            id="first-step",
            title="أول خطوة",
            description="خلّصت التقييم الأولي",
            earned=has_assessment,
        ),
        Badge(
            id="ready",
            title="جاهز تقنياً",
            description="كل صلاحياتك مفعّلة",
            earned=access_done,
        ),
        Badge(
            id="half-way",
            title="نص الطريق",
            description="أنجزت نص مسارك",
            earned=percent >= 50,
        ),
        Badge(
            id="policies",
            title="متقن السياسات",
            description=f"كل مواضيع التقييم فوق {PASSING_SCORE}",
            earned=topics_done,
        ),
        Badge(id="tamam", title="تمّام", description="أكملت مسارك كامل", earned=percent == 100),
    ]


def build_progress(employee_id: str) -> Progress:
    employee = get_employee(employee_id)
    statuses = access_statuses(employee)
    scores = latest_scores(assessment_results(employee_id))

    access_active = sum(1 for status in statuses.values() if status == "active")
    topics_passed = sum(1 for score in scores.values() if score >= PASSING_SCORE)
    total = len(statuses) + len(scores)
    done = access_active + topics_passed
    percent = 100 if total == 0 else round(done * 100 / total)

    return Progress(
        employee_id=employee_id,
        access_active=access_active,
        access_total=len(statuses),
        topics_passed=topics_passed,
        topics_total=len(scores),
        percent=percent,
        badges=build_badges(
            has_assessment=bool(scores),
            access_done=access_active == len(statuses),
            topics_done=bool(scores) and topics_passed == len(scores),
            percent=percent,
        ),
    )


def build_team(manager_id: str) -> list[TeamMember]:
    """The manager's direct reports, least progress first, each with their next step."""
    get_employee(manager_id)
    members: list[TeamMember] = []
    for employee in mock_data.EMPLOYEES:
        if employee.manager_id != manager_id:
            continue
        roadmap = build_roadmap(employee.id)
        # Meeting people is not a step to report on; the next access item or lesson is.
        steps = [i for w in roadmap.weeks for i in w.items if i.kind != "person"]
        members.append(
            TeamMember(
                employee=employee,
                progress=build_progress(employee.id),
                next_step=steps[0].title if steps else None,
            )
        )
    return sorted(members, key=lambda member: member.progress.percent)
