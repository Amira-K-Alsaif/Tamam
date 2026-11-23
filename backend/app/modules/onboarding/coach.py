"""The skill coach: a short conversation that teaches one skill and follows the employee's level.

The coach explains one idea at a time with an example from the employee's work, then asks a
question. With every reply it also judges the employee's level from their answers. Once they
have answered enough, the server moves the skill profile one step toward that judgement, and
the coach says so in its reply, so the level rises inside the conversation itself.

The conversation is sent by the page each time and is not stored; only the level is.
Skills are general knowledge, so the coach refers company questions to the chat.
"""

import json
import re

from pydantic import BaseModel, Field, ValidationError

from app.ai import llm

from . import prompts, service, skill_profile, specialization
from .schemas import CoachMessage, CoachReply, LevelChange

# Answers the employee must give before the coach may change their level.
MIN_ANSWERS = 3
# How far one reply can move the level, up or down.
MAX_STEP = 1

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")
_SPEAKERS = {"employee": "الموظف", "coach": "تمّام"}


class CoachUnavailableError(RuntimeError):
    """The model is not configured or did not answer."""


class _Reply(BaseModel):
    text: str = Field(min_length=1)
    level: int | None = Field(default=None, ge=0, le=4)


def _skill(employee_id: str, skill_id: int) -> specialization.Skill:
    """Only a skill of the employee's title or profile can be coached."""
    employee = service.get_employee(employee_id)
    allowed = {skill.id for skill in specialization.title_skills(employee.job_title)}
    allowed |= set(skill_profile.profile(employee_id))
    if skill_id not in allowed:
        raise LookupError(f"Skill {skill_id} is not one of this employee's skills")
    return specialization.by_id(skill_id)


def _transcript(messages: list[CoachMessage]) -> str:
    return "\n".join(f"{_SPEAKERS[m.role]}: {m.text.strip()}" for m in messages)


def _parse(raw: str) -> _Reply:
    """The coach's reply. A reply that is not the expected JSON is still shown, as plain text,
    but changes no level: only a well-formed judgement can move it."""
    try:
        return _Reply.model_validate(json.loads(_FENCE.sub("", raw.strip())))
    except (json.JSONDecodeError, ValidationError):
        return _Reply(text=raw.strip() or "…")


def reply(employee_id: str, skill_id: int, messages: list[CoachMessage]) -> CoachReply:
    """The coach's next message, and the level change it made, if any."""
    skill = _skill(employee_id, skill_id)
    employee = service.get_employee(employee_id)
    row = skill_profile.profile(employee_id).get(skill_id)
    previous = row.level if row else 0
    needed = specialization.expected_levels(employee.job_title).get(skill_id)
    can_update = sum(1 for m in messages if m.role == "employee") >= MIN_ANSWERS

    prompt = prompts.build_coach_prompt(
        skill.label_ar, previous, needed, employee.job_title, can_update, _transcript(messages)
    )
    try:
        raw = llm.generate(prompts.COACH_SYSTEM, prompt, fast=True)
    except (llm.LLMNotConfiguredError, llm.LLMUnavailableError) as error:
        raise CoachUnavailableError(str(error)) from error
    parsed = _parse(raw)

    change = None
    if can_update and parsed.level is not None and parsed.level != previous:
        level = max(previous - MAX_STEP, min(parsed.level, previous + MAX_STEP))
        skill_profile.save(employee_id, {skill_id: level})
        change = LevelChange(previous_level=previous, level=level, needed_level=needed)
    return CoachReply(text=parsed.text, level_change=change)
