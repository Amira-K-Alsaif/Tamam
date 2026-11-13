"""Pipeline step 1: split documents into small chunks that remember their source.

Small chunks make search precise (each one is about a single topic) and let every
answer cite an exact document, section, and page.
"""

from dataclasses import dataclass
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .sample_documents import DOCUMENTS


@dataclass(frozen=True)
class Chunk:
    """A searchable piece of a document. Matches the Chunk contract in docs/team.md."""

    id: str
    document_id: str
    document_title: str
    section_title: str
    page: int
    text: str


_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    # Repeats the end of one chunk at the start of the next, so no sentence loses its context.
    chunk_overlap=50,
    # Tried in order: paragraph, line, sentence, clause, then word.
    separators=["\n\n", "\n", ".", "؟", "،", " "],
)


def split_documents(documents: list[dict]) -> list[Chunk]:
    """Splits each section on its own, so a chunk never mixes two pages or topics."""
    chunks = []
    for document in documents:
        for section in document["sections"]:
            parts = _splitter.split_text(section["text"])
            for number, text in enumerate(parts, start=1):
                chunks.append(
                    Chunk(
                        id=f"{document['id']}-p{section['page']}-{number}",
                        document_id=document["id"],
                        document_title=document["title"],
                        section_title=section["title"],
                        page=section["page"],
                        text=text,
                    )
                )
    return chunks


@lru_cache
def all_chunks() -> tuple[Chunk, ...]:
    """Every chunk of the company documents, split once per process."""
    return tuple(split_documents(DOCUMENTS))
