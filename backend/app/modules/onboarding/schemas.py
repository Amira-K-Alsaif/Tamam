"""Shared data shapes owned by module 5 (onboarding). See docs/team.md."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["employee", "admin"]
AccessStatus = Literal["active", "requested", "missing"]


class EmployeeProfile(BaseModel):
    """Used by modules 3, 4, 5, 6."""

    id: str
    full_name: str
    department_id: str
    team: str
    job_title: str
    manager_id: str | None  # None only for the CEO
    years_of_experience: int = Field(ge=0)
    role: Role


class AccessItem(BaseModel):
    """A system or permission a job title needs. Used by modules 3, 5."""

    id: str
    system_name: str
    required_for_job_titles: list[str]
    procedure_id: str
    approver_role: str
    expected_days: int = Field(ge=0)


class EmployeeAccess(BaseModel):
    """The per-employee status of one access item."""

    employee_id: str
    access_item_id: str
    status: AccessStatus


class AssessmentResult(BaseModel):
    """One topic score from the starting assessment. Used by modules 5, 6."""

    employee_id: str
    topic: str
    score: int = Field(ge=0, le=100)
    taken_at: datetime
