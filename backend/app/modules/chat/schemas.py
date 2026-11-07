from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class Source(BaseModel):
    document_id: str
    document_title: str
    page: int
    section_title: str
    quote: str


class AskResponse(BaseModel):
    answer: str
    found: bool
    sources: list[Source]