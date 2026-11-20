"""Turns one company document into a validated Procedure.

The model's output is rejected unless every text it returns is really in the document,
so a procedure can never contain an invented step source, form name, or duration.
"""

import json
import re

from pydantic import ValidationError

from app.ai import llm
from app.ai.arabic import normalize_arabic

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import ExtractedProcedure, ExtractionResult, Procedure, Source

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")
_SECTIONS = re.compile(r"^#{1,6}\s+", re.MULTILINE)


class ExtractionError(ValueError):
    """The model's output was not valid JSON, did not match the schema, or was not grounded."""


def extract_procedure(
    *, document_id: str, title: str, department: str, text: str
) -> Procedure | None:
    """Returns the document's procedure, or None when it describes no procedure."""
    raw = llm.generate(SYSTEM_PROMPT, build_user_prompt(title, text))
    extracted = _parse(raw)
    if extracted is None:
        return None
    _check_grounded(extracted, text)
    return Procedure(
        id=document_id,
        title=title,
        department=department,
        summary=extracted.summary,
        owner=extracted.owner,
        duration_text=extracted.duration_text,
        requirements=extracted.requirements,
        forms=extracted.forms,
        steps=sorted(extracted.steps, key=lambda step: step.order),
        source=Source(
            document_id=document_id,
            document_title=title,
            section_title=_section_of(extracted.evidence, text),
            quote=extracted.evidence,
        ),
    )


def _parse(raw: str) -> ExtractedProcedure | None:
    try:
        return ExtractionResult.model_validate(json.loads(_FENCE.sub("", raw.strip()))).procedure
    except (json.JSONDecodeError, ValidationError) as error:
        raise ExtractionError(f"Model output is not a valid procedure: {error}") from error


def _check_grounded(extracted: ExtractedProcedure, text: str) -> None:
    document = normalize_arabic(text)
    copied = [extracted.evidence, extracted.duration_text, extracted.owner, *extracted.forms]
    for value in copied:
        if value and normalize_arabic(value) not in document:
            raise ExtractionError(f"Not found in the document: {value!r}")


def _section_of(quote: str, text: str) -> str | None:
    """The heading of the section that contains the quote, or None."""
    wanted = normalize_arabic(quote)
    for section in _SECTIONS.split(text):
        heading, _, body = section.partition("\n")
        if wanted in normalize_arabic(body):
            return heading.strip()
    return None
