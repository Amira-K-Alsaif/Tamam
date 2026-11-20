"""Company forms, read straight from their documents so no field is ever invented.

A form document lists its fields in a «الحقول» section, separated by «،», and how to
submit it in a «تعليمات» section. No language model is involved.
"""

import json
import re

from app.ai.arabic import normalize_arabic

from .schemas import CompanyForm, FieldKind, FormField, ProfileKey, Source
from .service import PROJECT_ROOT

MANIFEST_PATH = PROJECT_ROOT / "data/company/manifest.json"

FIELDS_SECTION = "الحقول"
INSTRUCTIONS_SECTION = "تعليمات"

_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_SEPARATORS = re.compile(r"[،,]")

# Fields the employee's profile already answers. Matched after Arabic normalization.
_PREFILL: dict[str, ProfileKey] = {
    normalize_arabic("اسم الموظف"): "full_name",
    normalize_arabic("الرقم الوظيفي"): "employee_id",
}

# The first word of a label says what kind of answer it takes.
_KINDS: dict[str, FieldKind] = {
    normalize_arabic("تاريخ"): "date",
    normalize_arabic("عدد"): "number",
    normalize_arabic("قائمة"): "long_text",
}


class FormNotFoundError(LookupError):
    pass


class FormDocumentError(ValueError):
    """A form document has no «الحقول» section, so it cannot be filled."""


def list_forms() -> list[CompanyForm]:
    return [_read_form(entry) for entry in _form_entries()]


def get_form(form_id: str) -> CompanyForm:
    for entry in _form_entries():
        if entry["id"] == form_id:
            return _read_form(entry)
    raise FormNotFoundError(form_id)


def parse_form(*, document_id: str, title: str, department: str, text: str) -> CompanyForm:
    sections = _sections(text)
    fields_line = sections.get(normalize_arabic(FIELDS_SECTION))
    if not fields_line:
        raise FormDocumentError(f"{document_id} has no «{FIELDS_SECTION}» section")
    labels = [label.strip(" .") for label in _SEPARATORS.split(fields_line)]
    return CompanyForm(
        id=document_id,
        title=title,
        department=department,
        instructions=sections.get(normalize_arabic(INSTRUCTIONS_SECTION)),
        fields=[_field(label) for label in labels if label],
        source=Source(
            document_id=document_id,
            document_title=title,
            section_title=FIELDS_SECTION,
            quote=fields_line,
        ),
    )


def _form_entries() -> list[dict]:
    return [e for e in json.loads(MANIFEST_PATH.read_text("utf-8")) if e["kind"] == "form"]


def _read_form(entry: dict) -> CompanyForm:
    text = (MANIFEST_PATH.parent / entry["file_path"]).read_text("utf-8")
    return parse_form(
        document_id=entry["id"], title=entry["title"], department=entry["department"], text=text
    )


def _sections(text: str) -> dict[str, str]:
    """Section bodies by normalized heading, each collapsed to one line."""
    parts = _HEADING.split(text)
    # parts = [before the first heading, heading, body, heading, body, ...]
    return {
        normalize_arabic(heading): " ".join(body.split())
        for heading, body in zip(parts[1::2], parts[2::2], strict=True)
    }


def _field(label: str) -> FormField:
    normalized = normalize_arabic(label)
    first_word = normalized.split(" ", 1)[0]
    return FormField(
        label=label,
        kind=_KINDS.get(first_word, "text"),
        prefill_from=_PREFILL.get(normalized),
    )
