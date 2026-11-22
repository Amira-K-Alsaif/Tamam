"""The model draws the employee's first weeks from their assessment.

It receives only the gaps the assessment found (lessons on weak policies, skills below what
the title needs) and orders them into weeks with a reason for each. It cannot add an item:
any id it invents is dropped, and any gap it leaves out is placed by the rules after its plan.
Access and people to meet stay rule-based, since who needs which system is a company rule.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.ai import llm

from . import prompts
from .schemas import EmployeeProfile, RoadmapItem

logger = logging.getLogger(__name__)

ITEMS_PER_WEEK = 3

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class _LLMItem(BaseModel):
    kind: Literal["lesson", "skill"]
    id: str
    week: int = Field(ge=1)
    reason: str = Field(min_length=1)


class _LLMPlan(BaseModel):
    items: list[_LLMItem]


@dataclass(frozen=True)
class Placement:
    week: int
    reason: str


# The drawn plan per employee: where each lesson or skill goes, and why.
_plans: dict[str, dict[tuple[str, str], Placement]] = {}


def gap_id(item: RoadmapItem) -> tuple[str, str]:
    return (item.kind, item.document_id if item.kind == "lesson" else str(item.skill_id))


def _describe(item: RoadmapItem) -> dict:
    kind, item_id = gap_id(item)
    if kind == "lesson":
        return {"kind": kind, "id": item_id, "title": item.topic, "score": item.score}
    return {
        "kind": kind,
        "id": item_id,
        "title": item.title,
        "level": item.level,
        "expected_level": item.expected_level,
    }


def draw(employee: EmployeeProfile, lessons: list[RoadmapItem], skills: list[RoadmapItem]) -> bool:
    """Asks the model for the plan and keeps it. Returns False if no usable plan came back.

    Without a plan the roadmap still shows every gap, ordered by the rules, so a busy model
    delays nothing; the roadmap says which of the two ordered it.
    """
    gaps = lessons + skills
    _plans.pop(employee.id, None)
    if not gaps:
        return True
    profile = {"job_title": employee.job_title, "team": employee.team}
    system = prompts.ROADMAP_SYSTEM.format(per_week=ITEMS_PER_WEEK)
    try:
        raw = llm.generate(
            system, prompts.build_roadmap_prompt(profile, [_describe(g) for g in gaps])
        )
        parsed = _LLMPlan.model_validate(json.loads(_FENCE.sub("", raw.strip())))
    except (llm.LLMNotConfiguredError, llm.LLMUnavailableError) as error:
        logger.warning("Roadmap not drawn for %s, the model is unavailable: %s", employee.id, error)
        return False
    except (json.JSONDecodeError, ValidationError) as error:
        logger.warning("Roadmap not drawn for %s, the plan was invalid: %s", employee.id, error)
        return False

    known = {gap_id(gap) for gap in gaps}
    plan: dict[tuple[str, str], Placement] = {}
    for item in parsed.items:
        key = (item.kind, item.id)
        if key in known and key not in plan:
            plan[key] = Placement(week=item.week, reason=item.reason.strip())
    if not plan:
        return False
    _plans[employee.id] = plan
    return True


def placement(employee_id: str, item: RoadmapItem) -> Placement | None:
    return _plans.get(employee_id, {}).get(gap_id(item))


def has_plan(employee_id: str) -> bool:
    return employee_id in _plans


def clear() -> None:
    """Forgets every drawn plan; for tests."""
    _plans.clear()
