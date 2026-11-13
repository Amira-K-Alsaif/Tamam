"""Shared knowledge contracts from docs/team.md."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    title: str
    kind: Literal["policy", "procedure", "form", "faq"]
    department: str
    file_path: str
    status: str
    updated_at: date


class Chunk(BaseModel):
    id: str
    document_id: str
    section_title: str
    page: int | None = None
    text: str = Field(min_length=1)
    embedding: list[float] | None = None
