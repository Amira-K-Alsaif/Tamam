"""Onboarding roadmap: knowledge gaps, missing access, people to meet. See docs/team.md."""

from fastapi import APIRouter, HTTPException, Query

from . import assessment, coach, mock_data, quiz, service
from .schemas import (
    Assessment,
    AssessmentOutcome,
    CoachReply,
    CoachRequest,
    CurrentEmployee,
    EmployeeProfile,
    LevelCheck,
    Progress,
    Quiz,
    QuizAnswers,
    QuizResult,
    Roadmap,
    TeamMember,
)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# Until Supabase Auth exists, the demo may view the page as one of the demo employees. Any
# other id is refused, so this cannot be used to read an arbitrary employee's data.
EmployeeId = Query(None, description="Demo only: view the page as one of /demo-employees.")


def _resolve(employee_id: str | None) -> str:
    if employee_id is None:
        return mock_data.CURRENT_EMPLOYEE_ID
    if employee_id not in mock_data.DEMO_EMPLOYEE_IDS:
        raise HTTPException(status_code=404, detail="Unknown demo employee")
    return employee_id


@router.get("/me", response_model=CurrentEmployee)
def get_current_employee(employee_id: str | None = EmployeeId) -> CurrentEmployee:
    """The signed-in employee. Uses the mock employee until auth exists."""
    return service.get_current_employee(_resolve(employee_id))


@router.get("/roadmap", response_model=Roadmap)
def get_roadmap(employee_id: str | None = EmployeeId) -> Roadmap:
    """The employee's roadmap, grouped by week."""
    return service.build_roadmap(_resolve(employee_id))


@router.get("/progress", response_model=Progress)
def get_progress(employee_id: str | None = EmployeeId) -> Progress:
    """How far the employee is along the path, with their badges."""
    return service.build_progress(_resolve(employee_id))


@router.get("/team", response_model=list[TeamMember])
def get_team(employee_id: str | None = EmployeeId) -> list[TeamMember]:
    """The employee's direct reports and their progress (empty for non-managers)."""
    return service.build_team(_resolve(employee_id))


@router.get("/demo-employees", response_model=list[EmployeeProfile])
def get_demo_employees() -> list[EmployeeProfile]:
    """The employees the demo can switch between."""
    return [service.get_employee(i) for i in mock_data.DEMO_EMPLOYEE_IDS]


@router.get("/assessment", response_model=Assessment)
def get_assessment(employee_id: str | None = EmployeeId) -> Assessment:
    """The employee's starting assessment: their company and their specialization. No answers."""
    try:
        return assessment.get_assessment(_resolve(employee_id))
    except quiz.QuizUnavailableError as error:
        raise HTTPException(status_code=503, detail="Assessment unavailable") from error


@router.post("/assessment/attempt", response_model=AssessmentOutcome)
def answer_assessment(body: QuizAnswers, employee_id: str | None = EmployeeId) -> AssessmentOutcome:
    """Grades the assessment, records policy scores and skill levels, and draws the roadmap."""
    try:
        return assessment.grade_assessment(_resolve(employee_id), body.answers)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Open the assessment first") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail="One answer per question") from error


@router.get("/lessons/{document_id}/quiz", response_model=Quiz)
def get_lesson_quiz(document_id: str) -> Quiz:
    """A short quiz on the lesson, generated from its policy document. No answers inside."""
    try:
        return quiz.get_quiz(document_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Unknown lesson") from error
    except quiz.QuizUnavailableError as error:
        raise HTTPException(status_code=503, detail="Quiz unavailable") from error


@router.post("/lessons/{document_id}/attempt", response_model=QuizResult)
def answer_lesson_quiz(
    document_id: str, body: QuizAnswers, employee_id: str | None = EmployeeId
) -> QuizResult:
    """Grades the answers and records the score, so the roadmap reorders."""
    employee = _resolve(employee_id)
    try:
        return quiz.grade_quiz(employee, document_id, body.answers)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Open the quiz first") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail="One answer per question") from error


@router.post("/skills/{skill_id}/coach", response_model=CoachReply)
def coach_reply(
    skill_id: int, body: CoachRequest, employee_id: str | None = EmployeeId
) -> CoachReply:
    """The skill coach's next message. The conversation is sent each time and not stored."""
    try:
        return CoachReply(text=coach.reply(_resolve(employee_id), skill_id, body.messages))
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Not one of your skills") from error
    except coach.CoachUnavailableError as error:
        raise HTTPException(status_code=503, detail="Coach unavailable") from error


@router.post("/skills/{skill_id}/level-check", response_model=LevelCheck)
def coach_level_check(
    skill_id: int, body: CoachRequest, employee_id: str | None = EmployeeId
) -> LevelCheck:
    """Judges the level from the employee's answers and updates their skill profile."""
    try:
        return coach.check_level(_resolve(employee_id), skill_id, body.messages)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Not one of your skills") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Answer a few questions first") from error
    except coach.CoachUnavailableError as error:
        raise HTTPException(status_code=503, detail="Coach unavailable") from error
