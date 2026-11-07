"""The chat's RAG logic: split, search, and answer."""

import re
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ai import embeddings, llm

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .sample_documents import DOCUMENTS
from .schemas import AskResponse, Source

# Low on purpose: the small model scores unrelated text near 0.8, so the model and the
# citation check do the real filtering. Raise it after switching to BGE-M3.
MIN_SCORE = 0.70
TOP_K = 3
NOT_FOUND = "ما لقيت هذي المعلومة في وثائق الشركة."

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", "؟", "،", " "],
)


def split_documents() -> list[dict]:
    chunks = []
    for document in DOCUMENTS:
        for section in document["sections"]:
            parts = splitter.split_text(section["text"])
            for number, text in enumerate(parts, start=1):
                chunks.append(
                    {
                        "id": f"{document['id']}-p{section['page']}-{number}",
                        "document_id": document["id"],
                        "document_title": document["title"],
                        "section_title": section["title"],
                        "page": section["page"],
                        "text": text,
                    }
                )
    return chunks


@lru_cache
def indexed_chunks() -> tuple[list[dict], list[list[float]]]:
    chunks = split_documents()
    vectors = embeddings.embed_passages([chunk["text"] for chunk in chunks])
    return chunks, vectors


def search(question: str, k: int = 3) -> list[tuple[float, dict]]:
    chunks, vectors = indexed_chunks()
    query = embeddings.embed_query(question)
    scored = [
        (sum(a * b for a, b in zip(vector, query, strict=True)), chunk)
        for vector, chunk in zip(vectors, chunks, strict=True)
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


def not_found() -> AskResponse:
    return AskResponse(answer=NOT_FOUND, found=False, sources=[])


def to_source(chunk: dict) -> Source:
    return Source(
        document_id=chunk["document_id"],
        document_title=chunk["document_title"],
        page=chunk["page"],
        section_title=chunk["section_title"],
        quote=chunk["text"],
    )


def answer(question: str) -> AskResponse:
    results = [(score, chunk) for score, chunk in search(question, TOP_K) if score >= MIN_SCORE]
    if not results:
        return not_found()

    chunks = [chunk for _, chunk in results]
    text = llm.generate(SYSTEM_PROMPT, build_user_prompt(question, chunks))

    cited = {int(n) for n in re.findall(r"\[(\d+)\]", text)}
    if not cited or not cited <= set(range(1, len(chunks) + 1)):
        return not_found()

    return AskResponse(
        answer=text,
        found=True,
        sources=[to_source(chunks[n - 1]) for n in sorted(cited)],
    )
