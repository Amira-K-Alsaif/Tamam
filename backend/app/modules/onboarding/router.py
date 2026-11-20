"""Onboarding roadmap: knowledge gaps, missing access, people to meet. See docs/team.md."""

from fastapi import APIRouter, HTTPException, Query

from . import mock_data, quiz, service
from .schemas import (
    CurrentEmployee,
    EmployeeProfile,
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
