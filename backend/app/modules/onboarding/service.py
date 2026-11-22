"""Builds the onboarding roadmap: knowledge and skill gaps, missing access, and people to meet."""

from datetime import UTC, datetime

from . import documents, mock_data, roadmap_ai, skill_profile, specialization
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
# Without a drawn plan: how many lessons or skills go in each week, weakest first.
LESSONS_PER_WEEK = 2
# A new hire's first step, before their lessons are known.
STARTING_ASSESSMENT = "التقييم الأولي"
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


# Scores recorded during this run of the server: the starting assessment and quiz retakes.
# The newest score per topic counts, so the roadmap reorders as quizzes are retaken.
# Moves to Supabase later.
_recorded: list[AssessmentResult] = []


def assessment_results(employee_id: str) -> list[AssessmentResult]:
    return [result for result in _recorded if result.employee_id == employee_id]


# Employees who took the starting assessment during this run of the server.
_assessed: set[str] = set()


def mark_assessed(employee_id: str) -> None:
    _assessed.add(employee_id)


def has_assessment(employee_id: str) -> bool:
    """Whether the employee has taken the starting assessment, so the roadmap has its gaps."""
    return employee_id in _assessed or bool(assessment_results(employee_id))


def record_scores(
    employee_id: str, scores: dict[str, int], taken_at: datetime | None = None
) -> None:
    get_employee(employee_id)
    when = taken_at or datetime.now(UTC)
    _recorded.extend(
        AssessmentResult(employee_id=employee_id, topic=topic, score=score, taken_at=when)
        for topic, score in scores.items()
    )


def record_quiz_score(employee_id: str, topic: str, score: int) -> None:
    record_scores(employee_id, {topic: score})


def clear_quiz_scores() -> None:
    """Forgets every recorded score; for tests and for restarting a demo."""
    _recorded.clear()
    _assessed.clear()


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
            document_id=documents.document_for(topic),
        )
        for index, (topic, score) in enumerate(weak)
    ]


def skill_gaps(employee_id: str) -> list[RoadmapItem]:
    """Measured skills below the level the employee's title needs, biggest gap first."""
    employee = get_employee(employee_id)
    expected = specialization.expected_levels(employee.job_title)
    measured = skill_profile.profile(employee_id)
    gaps = sorted(
        (
            (row, expected[skill_id])
            for skill_id, row in measured.items()
            if row.source == "assessment"
            and skill_id in expected
            and row.level < expected[skill_id]
        ),
        key=lambda pair: pair[0].level - pair[1],
    )
    return [
        RoadmapItem(
            kind="skill",
            title=specialization.by_id(row.skill_id).label_ar,
            reason=f"مستواك {row.level} من 4، ومسماك يحتاج {needed}.",
            week=index // LESSONS_PER_WEEK + 1,
            skill_id=row.skill_id,
            level=row.level,
            expected_level=needed,
        )
        for index, (row, needed) in enumerate(gaps)
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


def _place(employee_id: str, gaps: list[RoadmapItem]) -> list[RoadmapItem]:
    """Puts each gap where the drawn plan says, with its reason; the rest go after the plan."""
    planned = [(gap, roadmap_ai.placement(employee_id, gap)) for gap in gaps]
    last_week = max((place.week for _, place in planned if place), default=0)
    placed: list[RoadmapItem] = []
    for gap, place in planned:
        if place:
            placed.append(gap.model_copy(update={"week": place.week, "reason": place.reason}))
        else:
            placed.append(gap.model_copy(update={"week": last_week + gap.week}))
    return placed


def build_roadmap(employee_id: str) -> Roadmap:
    employee = get_employee(employee_id)
    access = missing_access(employee)
    gaps = knowledge_gaps(employee_id) + skill_gaps(employee_id)
    drawn = roadmap_ai.has_plan(employee_id)
    items = (
        access + people_to_meet(employee, access) + (_place(employee_id, gaps) if drawn else gaps)
    )

    weeks: dict[int, list[RoadmapItem]] = {}
    for item in items:
        weeks.setdefault(item.week, []).append(item)
    return Roadmap(
        employee_id=employee_id,
        assessed=has_assessment(employee_id),
        drawn_by="ai" if drawn else "rules",
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
        Badge(
            id="tamam",
            title="تمّام",
            description="أكملت مسارك كامل",
            # Without the assessment there are no lessons yet, so the path is not complete.
            earned=has_assessment and percent == 100,
        ),
    ]


def build_progress(employee_id: str) -> Progress:
    employee = get_employee(employee_id)
    statuses = access_statuses(employee)
    scores = latest_scores(assessment_results(employee_id))

    expected = specialization.expected_levels(employee.job_title)
    measured = {
        skill_id: row.level
        for skill_id, row in skill_profile.profile(employee_id).items()
        if row.source == "assessment" and skill_id in expected
    }

    access_active = sum(1 for status in statuses.values() if status == "active")
    topics_passed = sum(1 for score in scores.values() if score >= PASSING_SCORE)
    skills_ready = sum(1 for skill_id, level in measured.items() if level >= expected[skill_id])
    total = len(statuses) + len(scores) + len(measured)
    done = access_active + topics_passed + skills_ready
    percent = 100 if total == 0 else round(done * 100 / total)
    assessed = has_assessment(employee_id)

    return Progress(
        employee_id=employee_id,
        access_active=access_active,
        access_total=len(statuses),
        topics_passed=topics_passed,
        topics_total=len(scores),
        skills_ready=skills_ready,
        skills_total=len(measured),
        percent=percent,
        badges=build_badges(
            has_assessment=assessed,
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
        steps = [i.title for w in roadmap.weeks for i in w.items if i.kind != "person"]
        if not has_assessment(employee.id):
            steps.insert(0, STARTING_ASSESSMENT)
        members.append(
            TeamMember(
                employee=employee,
                progress=build_progress(employee.id),
                next_step=steps[0] if steps else None,
            )
        )
    return sorted(members, key=lambda member: member.progress.percent)
