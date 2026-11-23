"""The skill coach: a short conversation that teaches one skill at the employee's level.

The coach explains one idea at a time with an example from the employee's work, then asks a
question or sets a small exercise. After a few answers the employee can ask for their level:
the model judges it from their answers only, and the skill profile moves one step at most
toward that judgement, so one good or bad conversation cannot swing the level.

The conversation is sent by the page each time and is not stored; only the level is.
Skills are general knowledge, so the coach refers company questions to the chat.
"""

import json
import re

from pydantic import BaseModel, Field, ValidationError

from app.ai import llm

from . import prompts, service, skill_profile, specialization
from .schemas import CoachMessage, LevelCheck

# Answers the employee must give before their level can be judged.
MIN_ANSWERS = 3
# How far one check can move the level, up or down.
MAX_STEP = 1

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")
_SPEAKERS = {"employee": "الموظف", "coach": "تمّام"}


class CoachUnavailableError(RuntimeError):
    """The model is not configured, did not answer, or returned an unusable judgement."""


class _Judgement(BaseModel):
    level: int = Field(ge=0, le=4)
    reason: str = Field(min_length=1)


def _skill(employee_id: str, skill_id: int) -> specialization.Skill:
    """Only a skill of the employee's title or profile can be coached."""
    employee = service.get_employee(employee_id)
    allowed = {skill.id for skill in specialization.title_skills(employee.job_title)}
    allowed |= set(skill_profile.profile(employee_id))
    if skill_id not in allowed:
        raise LookupError(f"Skill {skill_id} is not one of this employee's skills")
    return specialization.by_id(skill_id)


def _level(employee_id: str, skill_id: int) -> int:
    row = skill_profile.profile(employee_id).get(skill_id)
    return row.level if row else 0


def _transcript(messages: list[CoachMessage]) -> str:
    return "\n".join(f"{_SPEAKERS[m.role]}: {m.text.strip()}" for m in messages)


def _ask(system: str, user: str) -> str:
    try:
        return llm.generate(system, user, fast=True).strip()
    except (llm.LLMNotConfiguredError, llm.LLMUnavailableError) as error:
        raise CoachUnavailableError(str(error)) from error


def reply(employee_id: str, skill_id: int, messages: list[CoachMessage]) -> str:
    """The coach's next message; with no messages, the opening one."""
    skill = _skill(employee_id, skill_id)
    employee = service.get_employee(employee_id)
    prompt = prompts.build_coach_prompt(
        skill.label_ar, _level(employee_id, skill_id), employee.job_title, _transcript(messages)
    )
    return _ask(prompts.COACH_SYSTEM, prompt)


def check_level(employee_id: str, skill_id: int, messages: list[CoachMessage]) -> LevelCheck:
    """Judges the level from the employee's answers and moves the profile one step toward it."""
    skill = _skill(employee_id, skill_id)
    if sum(1 for m in messages if m.role == "employee") < MIN_ANSWERS:
        raise ValueError(f"Answer at least {MIN_ANSWERS} times before checking the level")
    employee = service.get_employee(employee_id)
    previous = _level(employee_id, skill_id)

    raw = _ask(
        prompts.LEVEL_CHECK_SYSTEM,
        prompts.build_coach_prompt(
            skill.label_ar, previous, employee.job_title, _transcript(messages)
        ),
    )
    try:
        judged = _Judgement.model_validate(json.loads(_FENCE.sub("", raw)))
    except (json.JSONDecodeError, ValidationError) as error:
        raise CoachUnavailableError("The model did not return a level") from error

    level = max(previous - MAX_STEP, min(judged.level, previous + MAX_STEP))
    skill_profile.save(employee_id, {skill_id: level})
    return LevelCheck(
        level=level,
        previous_level=previous,
        expected_level=specialization.expected_levels(employee.job_title).get(skill_id),
        reason=judged.reason.strip(),
    )
