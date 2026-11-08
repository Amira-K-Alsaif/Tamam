"""Career path (مساري المهني): job-title skill profiles and gap analysis. See docs/team.md."""

from fastapi import APIRouter, HTTPException, Query

from . import service
from .repository import get_repository
from .schemas import GapAnalysis, JobTitle, TitleSkill

router = APIRouter(prefix="/api/career", tags=["career"])


@router.get("/titles", response_model=list[JobTitle])
def list_titles() -> list[JobTitle]:
    return service.list_titles(get_repository())


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
