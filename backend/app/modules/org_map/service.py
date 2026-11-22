"""Company map rules: who is in each department, how they relate to the viewer, and who
to contact about a topic."""

from app.ai.arabic import normalize_arabic

from . import mock_data
from .schemas import (
    DepartmentDetail,
    DepartmentSummary,
    Employee,
    OrgOverview,
    PersonDetail,
    PersonSummary,
    ProcedureRef,
    Relation,
    SearchHit,
    SearchResponse,
    TeamSummary,
)

# Words that carry no meaning in "who do I talk to about X?" questions.
_STOPWORDS = {
    normalize_arabic(word)
    for word in ["مين", "من", "أكلم", "اكلم", "أتواصل", "عن", "مع", "وش", "ابي", "أبي", "في"]
}
_PREFIXES = ("وال", "بال", "لل", "ال")
_SUFFIXES = ("ات", "ين", "ون", "ه")
# Search weights: a contact topic says the most about who to talk to.
_TOPIC_WEIGHT = 3
_PROCEDURE_WEIGHT = 2
_TITLE_WEIGHT = 1
MAX_HITS = 5


class NotFoundError(LookupError):
    pass


def _employee(employee_id: str) -> Employee:
    for employee in mock_data.EMPLOYEES:
        if employee.id == employee_id:
            return employee
    raise NotFoundError(employee_id)


def _department(department_id: str):
    for department in mock_data.DEPARTMENTS:
        if department.id == department_id:
            return department
    raise NotFoundError(department_id)


def _headcount(department_id: str) -> int:
    return sum(mock_data.TEAM_SIZES.get(department_id, {}).values())


def relation_to(person: Employee, viewer: Employee) -> Relation | None:
    if person.id == viewer.id:
        return "self"
    if person.id == viewer.manager_id:
        return "manager"
    if person.id == mock_data.MENTORS.get(viewer.id):
        return "mentor"
    return None


def _summary(person: Employee, viewer: Employee) -> PersonSummary:
    return PersonSummary(
        id=person.id,
        full_name=person.full_name,
        gender=person.gender,
        job_title=person.job_title,
        department_id=person.department_id,
        team=person.team,
        is_department_head=_department(person.department_id).head_id == person.id,
        relation=relation_to(person, viewer),
    )


def get_overview(viewer_id: str) -> OrgOverview:
    viewer = _employee(viewer_id)
    executive = _department(mock_data.EXECUTIVE_ID)
    departments = [d for d in mock_data.DEPARTMENTS if d.parent_id == executive.id]
    return OrgOverview(
        company_name=mock_data.COMPANY_NAME,
        employee_count=sum(_headcount(d.id) for d in departments),
        ceo=_summary(_employee(executive.head_id), viewer),
        departments=[
            DepartmentSummary(
                id=d.id,
                name=d.name,
                head=_summary(_employee(d.head_id), viewer),
                headcount=_headcount(d.id),
                is_mine=d.id == viewer.department_id,
            )
            for d in departments
        ],
        my_department_id=viewer.department_id,
        my_manager_id=viewer.manager_id,
    )


def get_department(department_id: str, viewer_id: str) -> DepartmentDetail:
    viewer = _employee(viewer_id)
    department = _department(department_id)
    members = [e for e in mock_data.EMPLOYEES if e.department_id == department.id]
    # The head comes first, then everyone in listing order.
    members.sort(key=lambda e: e.id != department.head_id)
    sizes = mock_data.TEAM_SIZES.get(department.id, {})
    return DepartmentDetail(
        id=department.id,
        name=department.name,
        headcount=_headcount(department.id),
        teams=[TeamSummary(name=team, size=sizes.get(team, 0)) for team in department.teams],
        members=[_summary(member, viewer) for member in members],
    )


def get_person(person_id: str, viewer_id: str) -> PersonDetail:
    viewer = _employee(viewer_id)
    person = _employee(person_id)
    responsibilities = [r for r in mock_data.RESPONSIBILITIES if r.employee_id == person.id]
    procedure_ids = list(dict.fromkeys(r.procedure_id for r in responsibilities if r.procedure_id))
    return PersonDetail(
        **_summary(person, viewer).model_dump(),
        department_name=_department(person.department_id).name,
        email=person.email,
        office=person.office,
        contact_topics=[r.topic for r in responsibilities],
        procedures=[
            ProcedureRef(id=pid, title=mock_data.PROCEDURE_TITLES.get(pid, pid))
            for pid in procedure_ids
        ],
    )


def _stem(word: str) -> str:
    for prefix in _PREFIXES:
        if word.startswith(prefix) and len(word) - len(prefix) >= 3:
            word = word[len(prefix) :]
            break
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            break
    return word


def _terms(text: str) -> set[str]:
    words = "".join(c if c.isalnum() else " " for c in normalize_arabic(text)).split()
    return {_stem(w) for w in words if w not in _STOPWORDS and len(w) > 1}


def search(query: str, viewer_id: str) -> SearchResponse:
    """Ranks people by how well their contact topics, procedures and titles match `query`."""
    viewer = _employee(viewer_id)
    wanted = _terms(query)
    # Per employee: the query terms they cover, their weighted score, and the label
    # that matched best.
    covered: dict[str, set[str]] = {}
    scores: dict[str, int] = {}
    best: dict[str, tuple[int, str]] = {}

    def add(employee_id: str, text: str, weight: int) -> None:
        overlap = wanted & _terms(text)
        if not overlap or employee_id == viewer.id:
            return
        points = len(overlap) * weight
        covered.setdefault(employee_id, set()).update(overlap)
        scores[employee_id] = scores.get(employee_id, 0) + points
        if points > best.get(employee_id, (0, ""))[0]:
            best[employee_id] = (points, text)

    for r in mock_data.RESPONSIBILITIES:
        add(r.employee_id, r.topic, _TOPIC_WEIGHT)
        if r.procedure_id:
            add(
                r.employee_id, mock_data.PROCEDURE_TITLES.get(r.procedure_id, ""), _PROCEDURE_WEIGHT
            )
    for e in mock_data.EMPLOYEES:
        add(e.id, e.job_title, _TITLE_WEIGHT)

    # Covering more of the question beats matching one word many times.
    ranked = sorted(scores, key=lambda eid: (-len(covered[eid]), -scores[eid]))[:MAX_HITS]
    return SearchResponse(
        query=query,
        hits=[
            SearchHit(
                person=_summary(_employee(employee_id), viewer),
                department_name=_department(_employee(employee_id).department_id).name,
                matched_topic=best[employee_id][1],
            )
            for employee_id in ranked
        ],
    )
