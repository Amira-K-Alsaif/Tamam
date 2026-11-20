"""Shapes of the procedures API and of the model's extraction output."""

from typing import Literal

from pydantic import BaseModel, Field


class Step(BaseModel):
    order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)
    detail: str = Field(min_length=1)


class ExtractedProcedure(BaseModel):
    """What the model returns for one document. Every text field is copied from it."""

    summary: str = Field(min_length=1, max_length=300)
    owner: str | None = None
    duration_text: str | None = None
    requirements: list[str] = Field(default_factory=list)
    forms: list[str] = Field(default_factory=list)
    steps: list[Step] = Field(min_length=1)
    evidence: str = Field(min_length=1)


class ExtractionResult(BaseModel):
    """`procedure` is null when the document describes no procedure."""

    procedure: ExtractedProcedure | None = None


class Source(BaseModel):
    """Source citation contract from docs/team.md."""

    document_id: str
    document_title: str
    page: int | None = None
    section_title: str | None = None
    quote: str


FieldKind = Literal["text", "long_text", "date", "number"]

# Profile fields a form field can be filled from (Employee profile contract, docs/team.md).
ProfileKey = Literal["full_name", "employee_id"]


class FormField(BaseModel):
    label: str
    kind: FieldKind
    # Set when the value comes from the employee's profile; None means the employee types it.
    prefill_from: ProfileKey | None = None


class CompanyForm(BaseModel):
    id: str  # The form's document id, e.g. "leave-request-form".
    title: str
    department: str
    instructions: str | None
    fields: list[FormField]
    source: Source


class Procedure(BaseModel):
    id: str  # "proc-<document id>", the procedure_id other modules reference.
    title: str
    department: str
    summary: str
    owner: str | None
    duration_text: str | None
    requirements: list[str]
    forms: list[str]
    steps: list[Step]
    source: Source
