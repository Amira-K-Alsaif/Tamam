"""The development plan written by the model for one employee's gap, carried out alone.

The model receives only the real gap (skills the target title's postings ask for, with the
employee's level and the level needed) and writes concrete self-directed actions. It cannot add
a skill: actions on any other skill are dropped, as are unknown action types. It is told not to
name people, links, or courses. If it is unavailable or writes nothing usable, the caller falls
back to the rule-based plan (plan.py), and the plan says which one it is.
"""

import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.ai import llm

from . import prompts
from .repository import CareerRepository
from .schemas import DevelopmentPlan, GapAnalysis, PlanAction, PlanPhase

logger = logging.getLogger(__name__)

ACTIONS_PER_PHASE = 3
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")

# One plan per gap: the same titles and levels give the same plan without asking again.
_plans: dict[tuple, DevelopmentPlan] = {}


class _LLMAction(BaseModel):
    skill_id: int
    type: str
    title_ar: str = Field(min_length=1)
    steps_ar: list[str] = Field(default_factory=list)
    success_metric_ar: str = Field(min_length=1)
    effort_hours: int = Field(ge=1, le=40)


class _LLMPhase(BaseModel):
    phase: Literal["30", "60", "90"]
    goal_ar: str = Field(min_length=1)
    actions: list[_LLMAction]


class _LLMPlan(BaseModel):
    phases: list[_LLMPhase]


ALLOWED_TYPES = {"self_study", "practice", "project", "certification"}


def _key(gap: GapAnalysis) -> tuple:
    skills = [*gap.gap.missing, *gap.gap.to_improve]
    return (
        gap.current_title_id,
        gap.target_title_id,
        tuple(sorted((s.skill_id, s.employee_level, s.expected_level) for s in skills)),
    )


def _describe(gap: GapAnalysis) -> list[dict]:
    return [
        {
            "skill_id": s.skill_id,
            "skill": s.label_ar,
            "status": status,
            "level": s.employee_level,
            "needed": s.expected_level,
            "share_of_postings": round(s.market_frequency, 2),
        }
        for status, skills in (("missing", gap.gap.missing), ("improve", gap.gap.to_improve))
        for s in skills
    ]


def write_plan(repo: CareerRepository, gap: GapAnalysis) -> DevelopmentPlan | None:
    """The tailored plan, or None if the model could not write a usable one."""
    key = _key(gap)
    if key in _plans:
        return _plans[key]
    described = _describe(gap)
    if not described:
        return None

    prompt = prompts.build_plan_prompt(
        repo.titles[gap.current_title_id]["name_ar"],
        repo.titles[gap.target_title_id]["name_ar"],
        described,
    )
    try:
        raw = llm.generate(prompts.PLAN_SYSTEM, prompt, fast=True)
        parsed = _LLMPlan.model_validate(json.loads(_FENCE.sub("", raw.strip())))
    except (llm.LLMNotConfiguredError, llm.LLMUnavailableError) as error:
        logger.warning("Plan not written, the model is unavailable: %s", error)
        return None
    except (json.JSONDecodeError, ValidationError) as error:
        logger.warning("Plan not written, the model's plan was invalid: %s", error)
        return None

    gap_skills = {item["skill_id"] for item in described}
    phases: list[PlanPhase] = []
    for phase in sorted(parsed.phases, key=lambda p: p.phase):
        if any(p.phase == phase.phase for p in phases):
            continue
        actions = [
            PlanAction(
                skill_id=a.skill_id,
                type=a.type,
                title_ar=a.title_ar.strip(),
                steps_ar=[step.strip() for step in a.steps_ar if step.strip()][:4],
                effort_hours=a.effort_hours,
                success_metric_ar=a.success_metric_ar.strip(),
            )
            for a in phase.actions
            if a.skill_id in gap_skills and a.type in ALLOWED_TYPES
        ][:ACTIONS_PER_PHASE]
        if actions:
            phases.append(
                PlanPhase(phase=phase.phase, goal_ar=phase.goal_ar.strip(), actions=actions)
            )
    if not phases:
        return None

    plan = DevelopmentPlan(
        current_title_id=gap.current_title_id,
        target_title_id=gap.target_title_id,
        readiness_score=gap.readiness_score,
        low_evidence=gap.gap.low_evidence,
        phases=phases,
        written_by="ai",
    )
    _plans[key] = plan
    return plan


def clear() -> None:
    """Forgets written plans; for tests."""
    _plans.clear()
