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


class CurrentEmployee(EmployeeProfile):
    """The signed-in employee, as `GET /api/onboarding/me` returns it."""

    manager_name: str | None  # The manager's full_name; None only for the CEO


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


# Response shapes for the onboarding roadmap (module 5 only, not shared contracts).

RoadmapKind = Literal["lesson", "skill", "access", "person"]


class RoadmapItem(BaseModel):
    """One thing the new employee is missing, and why it is on the roadmap."""

    kind: RoadmapKind
    title: str
    reason: str
    week: int = Field(ge=1)
    # lesson
    score: int | None = None
    # access
    access_item_id: str | None = None
    status: AccessStatus | None = None
    procedure_id: str | None = None
    approver_role: str | None = None
    expected_days: int | None = None
    # person
    employee_id: str | None = None
    # lesson: the assessment topic and the policy document its quiz comes from
    topic: str | None = None
    document_id: str | None = None
    # skill
    skill_id: int | None = None
    level: int | None = None
    expected_level: int | None = None


class RoadmapWeek(BaseModel):
    week: int
    items: list[RoadmapItem]


class Roadmap(BaseModel):
    employee_id: str
    # False until the starting assessment is taken; the page shows the assessment first.
    assessed: bool
    # Who ordered the lessons and skills: the model from the assessment, or the rules.
    drawn_by: Literal["ai", "rules"]
    weeks: list[RoadmapWeek]


class Badge(BaseModel):
    """An achievement on the onboarding path (week 3 of the plan)."""

    id: str
    title: str
    description: str
    earned: bool


class Progress(BaseModel):
    """How far an employee is along the path, counted in access items and assessment topics."""

    employee_id: str
    access_active: int
    access_total: int
    topics_passed: int
    topics_total: int
    skills_ready: int  # Measured skills at the level the title needs
    skills_total: int
    percent: int = Field(ge=0, le=100)
    badges: list[Badge]


class TeamMember(BaseModel):
    """One direct report on the manager's dashboard (week 4 of the plan)."""

    employee: EmployeeProfile
    progress: Progress
    next_step: str | None


class SourceCitation(BaseModel):
    """Where a quiz question comes from. Matches the shared source citation contract."""

    document_id: str
    document_title: str
    page: int | None
    section_title: str
    quote: str


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=2, max_length=4)
    source: SourceCitation


class Quiz(BaseModel):
    """A short quiz on one lesson, generated from its policy document. No answers inside."""

    topic: str
    document_id: str
    document_title: str
    questions: list[QuizQuestion]


class QuizAnswers(BaseModel):
    """The option index the employee chose for each question, in order."""

    answers: list[int]


class QuizResult(BaseModel):
    topic: str
    score: int = Field(ge=0, le=100)
    passed: bool
    correct: list[bool]
    correct_options: list[int]


AssessmentKind = Literal["company", "skill"]


class AssessmentQuestion(BaseModel):
    """A starting-assessment question: on a company policy, or the employee's level in a skill.

    Company questions carry the policy sentence that proves the answer. Skill questions ask the
    employee to rate themselves, from «ما أعرفها» (0) to «خبير» (4), so they have no right answer.
    """

    kind: AssessmentKind
    topic: str  # The policy's title, or the skill's Arabic name
    question: str
    options: list[str] = Field(min_length=2, max_length=5)
    source: SourceCitation | None = None
    skill_id: int | None = None


class Assessment(BaseModel):
    """The starting assessment for one employee."""

    questions: list[AssessmentQuestion]


class TopicScore(BaseModel):
    topic: str
    document_id: str
    score: int = Field(ge=0, le=100)
    passed: bool


class SkillResult(BaseModel):
    skill_id: int
    label_ar: str
    level: int = Field(ge=0, le=4)
    expected_level: int | None  # What the employee's title needs; None if the title is unknown


class AssessmentOutcome(BaseModel):
    """Scores per policy and a level per skill; the roadmap is drawn from them."""

    topics: list[TopicScore]
    skills: list[SkillResult]
    # None for the self-rated skill questions, which have no right answer.
    correct: list[bool | None]
    correct_options: list[int | None]
