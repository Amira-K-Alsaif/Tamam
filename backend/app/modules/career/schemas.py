"""API contract of the career module (مساري المهني)."""

from typing import Literal

from pydantic import BaseModel, Field


class JobTitle(BaseModel):
    id: int
    code: str
    ladder: str
    level: str
    name_ar: str
    name_en: str
    next_title_id: int | None
    esco_occupation_uri: str | None  # ESCO occupation, European Commission
    postings_count: int


class TitleSkill(BaseModel):
    skill_id: int
    esco_id: str | None
    label_ar: str
    label_en: str
    category: str
    frequency: float = Field(ge=0, le=1)
    required_ratio: float = Field(ge=0, le=1)
    postings_count: int


class GapSkill(BaseModel):
    skill_id: int
    label_ar: str
    label_en: str
    market_frequency: float
    expected_level: int = Field(ge=1, le=5)
    employee_level: int = Field(ge=0, le=5)


class MissingSkill(GapSkill):
    priority: Literal["high", "medium", "low"]


class Gap(BaseModel):
    matched: list[GapSkill]
    missing: list[MissingSkill]
    to_improve: list[GapSkill]
    evidence_postings: int
    low_evidence: bool  # Too few target postings for the profile to be reliable


LevelSource = Literal["employee_profile", "current_title_market_proxy"]


class GapAnalysis(BaseModel):
    current_title_id: int
    target_title_id: int
    readiness_score: float = Field(ge=0, le=100)
    level_source: LevelSource
    gap: Gap
    radar: list[GapSkill]


ActionType = Literal["course", "project", "mentoring", "shadowing", "certification", "reading"]


class PlanAction(BaseModel):
    skill_id: int
    type: ActionType
    title_ar: str
    effort_hours: int = Field(ge=1)
    success_metric_ar: str


class PlanPhase(BaseModel):
    phase: Literal["30", "60", "90"]
    goal_ar: str
    actions: list[PlanAction]


class DevelopmentPlan(BaseModel):
    """A 30/60/90-day plan built from the gap (masari_api_contract.json → plan)."""

    current_title_id: int
    target_title_id: int
    readiness_score: float = Field(ge=0, le=100)
    low_evidence: bool
    phases: list[PlanPhase]
