"""Reads an employee's CV and finds their skills in it.

The CV text is used once and not stored: only the skills found, with the sentence that shows
each one, go into the employee's skill profile. A skill is kept only when its key is in the
dictionary and its quote is really in the CV, so the model cannot add a skill the CV does not
show, and a CV that gives orders cannot award itself skills.
"""

import json
import re
import tempfile
from pathlib import Path

from pydantic import BaseModel, ValidationError

from app.ai import llm
from app.ai.arabic import normalize_arabic

from . import prompts, skill_profile, specialization
from .schemas import CvSkill

MAX_BYTES = 2 * 1024 * 1024
TEXT_TYPES = {".txt", ".md"}
DOCUMENT_TYPES = {".pdf", ".docx"}
# A CV only says the employee has a skill, not how well; the assessment measures the level.
CV_LEVEL = 1

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class CvError(ValueError):
    """The file is not a CV Tamam can read."""


class CvUnavailableError(RuntimeError):
    """The model is not configured, did not answer, or returned no usable list."""


class _LLMSkill(BaseModel):
    key: str
    quote: str


class _LLMSkills(BaseModel):
    skills: list[_LLMSkill]


def read_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if len(data) > MAX_BYTES:
        raise CvError("The CV is larger than 2 MB")
    if suffix in TEXT_TYPES:
        text = data.decode("utf-8", errors="replace")
    elif suffix in DOCUMENT_TYPES:
        text = _convert(suffix, data)
    else:
        raise CvError(f"Unsupported CV type: {suffix}")
    if not text.strip():
        raise CvError("The CV has no readable text")
    return text


def _convert(suffix: str, data: bytes) -> str:
    # Import on demand: ordinary backend checks do not load a document conversion model.
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as error:
        raise CvUnavailableError("Reading PDF and Word CVs needs the approved Docling") from error

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / f"cv{suffix}"
        path.write_bytes(data)
        conversion = DocumentConverter().convert(str(path))
        try:
            return conversion.document.export_to_markdown()
        finally:
            conversion.input.release()


def _comparable(text: str) -> str:
    return " ".join(normalize_arabic(text).split())


def extract_skills(text: str) -> list[CvSkill]:
    dictionary = specialization.dictionary()
    listed = [(skill.key, skill.label_ar, skill.label_en) for skill in dictionary.values()]
    try:
        raw = llm.generate(prompts.CV_SYSTEM, prompts.build_cv_prompt(listed, text))
    except (llm.LLMNotConfiguredError, llm.LLMUnavailableError) as error:
        raise CvUnavailableError(str(error)) from error
    try:
        parsed = _LLMSkills.model_validate(json.loads(_FENCE.sub("", raw.strip())))
    except (json.JSONDecodeError, ValidationError) as error:
        raise CvUnavailableError("The model did not return a skill list") from error

    cv = _comparable(text)
    found: dict[str, CvSkill] = {}
    for item in parsed.skills:
        skill = dictionary.get(item.key)
        quote = _comparable(item.quote)
        if skill is None or not quote or quote not in cv or skill.key in found:
            continue
        found[skill.key] = CvSkill(skill_id=skill.id, label_ar=skill.label_ar, quote=item.quote)
    return list(found.values())


def read_cv(employee_id: str, filename: str, data: bytes) -> list[CvSkill]:
    """Finds the skills in the CV and records them in the employee's skill profile."""
    skills = extract_skills(read_text(filename, data))
    skill_profile.save(
        employee_id,
        {skill.skill_id: CV_LEVEL for skill in skills},
        source="cv",
        evidence={skill.skill_id: skill.quote for skill in skills},
    )
    return skills
