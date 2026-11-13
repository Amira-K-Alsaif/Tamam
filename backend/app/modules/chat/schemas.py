"""The chat API contract. The frontend mirrors these shapes in src/lib/api.ts."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class Source(BaseModel):
    """Where a part of the answer came from. Matches the Source citation contract in
    docs/team.md."""

    document_id: str
    document_title: str
    page: int
    section_title: str
    quote: str


class AskResponse(BaseModel):
    answer: str
    # False when the answer is the "not found" message; `sources` is then empty.
    found: bool
    sources: list[Source]
