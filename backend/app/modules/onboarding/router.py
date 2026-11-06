"""Onboarding roadmap: knowledge gaps, missing access, people to meet. See docs/team.md."""

from fastapi import APIRouter

from . import mock_data, service
from .schemas import EmployeeProfile, Roadmap

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("/me", response_model=EmployeeProfile)
def get_current_employee() -> EmployeeProfile:
    """The signed-in employee. Uses the mock employee until auth exists."""
    return service.get_employee(mock_data.CURRENT_EMPLOYEE_ID)


@router.get("/roadmap", response_model=Roadmap)
def get_roadmap() -> Roadmap:
    """The signed-in employee's roadmap, grouped by week."""
    return service.build_roadmap(mock_data.CURRENT_EMPLOYEE_ID)
