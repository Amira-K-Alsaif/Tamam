"""Career path (مساري المهني): job-title skill profiles and gap analysis. See docs/team.md."""

from fastapi import APIRouter, HTTPException, Query

from app.modules.onboarding import skill_profile

from . import plan, plan_ai, service
from .repository import get_repository
from .schemas import DevelopmentPlan, GapAnalysis, JobTitle, TitleSkill

router = APIRouter(prefix="/api/career", tags=["career"])

# Demo only until auth exists, as in onboarding: the page names the employee it shows.
EmployeeId = Query(None, description="Use this employee's measured skill levels when present.")


def _employee_skills(repo, current_title_id: int, employee_id: str | None) -> dict[int, int] | None:
    """The employee's skill profile, or None to estimate every level from the market."""
    measured = skill_profile.levels(employee_id) if employee_id else None
    if not measured:
        return None
    return service.employee_levels(repo, current_title_id, measured)


@router.get("/titles", response_model=list[JobTitle])
def list_titles() -> list[JobTitle]:
    return service.list_titles(get_repository())


@router.get("/titles/match", response_model=JobTitle)
def match_title(job_title: str = Query(min_length=1)) -> JobTitle:
    try:
        return service.match_title(get_repository(), job_title)
    except service.TitleNotFoundError as e:
        raise HTTPException(404, "ما عندنا إعلانات وظائف لهذا المسمى الوظيفي") from e


@router.get("/titles/{title_id}/skills", response_model=list[TitleSkill])
def title_skills(title_id: int) -> list[TitleSkill]:
    try:
        return service.title_skills(get_repository(), title_id)
    except service.TitleNotFoundError as e:
        raise HTTPException(404, "المسمى الوظيفي غير موجود") from e


@router.get("/gap-analysis", response_model=GapAnalysis)
def gap_analysis(
    current_title_id: int = Query(),
    target_title_id: int = Query(),
    employee_id: str | None = EmployeeId,
) -> GapAnalysis:
    if current_title_id == target_title_id:
        raise HTTPException(400, "اختاري منصباً مستهدفاً مختلفاً عن منصبك الحالي")
    repo = get_repository()
    try:
        skills = _employee_skills(repo, current_title_id, employee_id)
        return service.analyze_gap(repo, current_title_id, target_title_id, skills)
    except service.TitleNotFoundError as e:
        raise HTTPException(404, "المسمى الوظيفي غير موجود") from e


@router.get("/plan", response_model=DevelopmentPlan)
def development_plan(
    current_title_id: int = Query(),
    target_title_id: int = Query(),
    employee_id: str | None = EmployeeId,
) -> DevelopmentPlan:
    """A 30/60/90-day plan, carried out alone, for the skills the gap found missing or weak."""
    if current_title_id == target_title_id:
        raise HTTPException(400, "اختاري منصباً مستهدفاً مختلفاً عن منصبك الحالي")
    repo = get_repository()
    try:
        skills = _employee_skills(repo, current_title_id, employee_id)
        gap = service.analyze_gap(repo, current_title_id, target_title_id, skills)
    except service.TitleNotFoundError as e:
        raise HTTPException(404, "المسمى الوظيفي غير موجود") from e
    # The model writes a plan for this gap; the rule templates stand in when it cannot.
    return plan_ai.write_plan(repo, gap) or plan.build_plan(repo, gap)
