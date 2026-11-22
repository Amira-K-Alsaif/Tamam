"""Data shapes owned by module 4 (org-map). See docs/team.md."""

from typing import Literal

from pydantic import BaseModel, Field

Gender = Literal["f", "m"]
# How a person relates to the signed-in employee.
Relation = Literal["self", "manager", "mentor"]


class Department(BaseModel):
    """Shared contract, used by modules 4 and 5."""

    id: str
    name: str
    head_id: str
    parent_id: str | None  # None only for the executive office
    teams: list[str]


class ContactResponsibility(BaseModel):
    """Shared contract, used by modules 3, 4 and 5: what to contact an employee about."""

    employee_id: str
    topic: str
    procedure_id: str | None = None


class Employee(BaseModel):
    """The org-map view of an employee: the shared profile fields this module needs,
    plus contact details."""

    id: str
    full_name: str
    gender: Gender
    department_id: str
    team: str
    job_title: str
    manager_id: str | None
    email: str
    office: str


# Response shapes (module 4 only, not shared contracts).


class PersonSummary(BaseModel):
    id: str
    full_name: str
    gender: Gender
    job_title: str
    department_id: str
    team: str
    is_department_head: bool
    relation: Relation | None


class ProcedureRef(BaseModel):
    id: str
    title: str


class PersonDetail(PersonSummary):
    department_name: str
    email: str
    office: str
    contact_topics: list[str]
    procedures: list[ProcedureRef]


class DepartmentSummary(BaseModel):
    id: str
    name: str
    head: PersonSummary
    headcount: int = Field(ge=0)
    is_mine: bool


class OrgOverview(BaseModel):
    company_name: str
    employee_count: int = Field(ge=0)
    ceo: PersonSummary
    departments: list[DepartmentSummary]
    my_department_id: str
    my_manager_id: str | None


class TeamSummary(BaseModel):
    name: str
    size: int = Field(ge=0)


class DepartmentDetail(BaseModel):
    id: str
    name: str
    headcount: int = Field(ge=0)
    teams: list[TeamSummary]
    members: list[PersonSummary]


class SearchHit(BaseModel):
    person: PersonSummary
    department_name: str
    matched_topic: str


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
