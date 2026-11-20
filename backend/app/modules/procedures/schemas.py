"""Shapes of the procedures API and of the model's extraction output."""

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


class Procedure(BaseModel):
    id: str  # The document id, so other modules can reference it as procedure_id.
    title: str
    department: str
    summary: str
    owner: str | None
    duration_text: str | None
    requirements: list[str]
    forms: list[str]
    steps: list[Step]
    source: Source
