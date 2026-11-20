"""Career path (مساري المهني): job-title skill profiles and gap analysis. See docs/team.md."""

from fastapi import APIRouter, HTTPException, Query

from . import plan, service
from .repository import get_repository
from .schemas import DevelopmentPlan, GapAnalysis, JobTitle, TitleSkill

router = APIRouter(prefix="/api/career", tags=["career"])


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
def gap_analysis(current_title_id: int = Query(), target_title_id: int = Query()) -> GapAnalysis:
    if current_title_id == target_title_id:
        raise HTTPException(400, "اختاري منصباً مستهدفاً مختلفاً عن منصبك الحالي")
    try:
        return service.analyze_gap(get_repository(), current_title_id, target_title_id)
    except service.TitleNotFoundError as e:
        raise HTTPException(404, "المسمى الوظيفي غير موجود") from e


@router.get("/plan", response_model=DevelopmentPlan)
def development_plan(
    current_title_id: int = Query(), target_title_id: int = Query()
) -> DevelopmentPlan:
    """A 30/60/90-day plan for the skills the gap analysis found missing or weak."""
    if current_title_id == target_title_id:
        raise HTTPException(400, "اختاري منصباً مستهدفاً مختلفاً عن منصبك الحالي")
    repo = get_repository()
    try:
        gap = service.analyze_gap(repo, current_title_id, target_title_id)
    except service.TitleNotFoundError as e:
        raise HTTPException(404, "المسمى الوظيفي غير موجود") from e
    return plan.build_plan(repo, gap)
