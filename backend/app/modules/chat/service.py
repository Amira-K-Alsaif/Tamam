"""The chat's RAG logic: split, search, and answer."""

import re
from functools import lru_cache

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ai import embeddings, llm, reranker

from . import retrieval
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .sample_documents import DOCUMENTS
from .schemas import AskResponse, Source

# Low on purpose: the small model scores unrelated text near 0.8, so the model and the
# citation check do the real filtering. Raise it after switching to BGE-M3.
MIN_SCORE = 0.70
TOP_K = 3
# How many chunks the fast search hands to the slower, more accurate reranker.
CANDIDATES = 10
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
def all_chunks() -> list[dict]:
    return split_documents()


@lru_cache
def keyword_index() -> list[list[str]]:
    return [retrieval.tokenize(chunk["text"]) for chunk in all_chunks()]


@lru_cache
def indexed_chunks() -> tuple[list[dict], list[list[float]]]:
    chunks = all_chunks()
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


def keyword_search(question: str, k: int = 3) -> list[tuple[float, dict]]:
    scores = retrieval.bm25(retrieval.tokenize(question), keyword_index())
    scored = [
        (score, chunk) for score, chunk in zip(scores, all_chunks(), strict=True) if score > 0
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


def retrieve(question: str) -> list[dict]:
    """Hybrid search: chunks close in meaning plus chunks sharing exact words, merged by rank."""
    by_meaning = [chunk for score, chunk in search(question, CANDIDATES) if score >= MIN_SCORE]
    by_words = [chunk for _, chunk in keyword_search(question, CANDIDATES)]

    chunks_by_id = {chunk["id"]: chunk for chunk in by_meaning + by_words}
    merged = retrieval.reciprocal_rank_fusion(
        [[chunk["id"] for chunk in by_meaning], [chunk["id"] for chunk in by_words]]
    )
    return [chunks_by_id[chunk_id] for chunk_id in merged[:CANDIDATES]]


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
    candidates = retrieve(question)
    if not candidates:
        return not_found()

    scores = reranker.rerank(question, [chunk["text"] for chunk in candidates])
    ranked = sorted(zip(scores, candidates, strict=True), key=lambda pair: pair[0], reverse=True)
    chunks = [chunk for _, chunk in ranked[:TOP_K]]
    text = llm.generate(SYSTEM_PROMPT, build_user_prompt(question, chunks))

    cited = {int(n) for n in re.findall(r"\[(\d+)\]", text)}
    if not cited or not cited <= set(range(1, len(chunks) + 1)):
        return not_found()

    # Renumber the citations 1..n so they match the order of the returned sources.
    new_numbers = {old: new for new, old in enumerate(sorted(cited), start=1)}
    text = re.sub(r"\[(\d+)\]", lambda match: f"[{new_numbers[int(match[1])]}]", text)

    return AskResponse(
        answer=text,
        found=True,
        sources=[to_source(chunks[n - 1]) for n in sorted(cited)],
    )
