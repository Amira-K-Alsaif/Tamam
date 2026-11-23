"""Answers an employee's question from the company documents (Retrieval-Augmented
Generation). See README.md in this folder for the full walkthrough."""

from app.ai import llm
from app.config import get_settings

from . import citations, retrieval
from .corpus import Chunk
from .prompts import REWRITE_PROMPT, build_rewrite_prompt, build_system_prompt, build_user_prompt
from .schemas import AskResponse, Source

# How many chunks the model reads. One is too risky: an answer may need two chunks,
# and the best one is not always ranked first.
TOP_K = 3
NOT_FOUND = "ما لقيت هذي المعلومة في وثائق الشركة."


def answer(question: str) -> AskResponse:
    chunks = find_chunks(question)
    if not chunks:
        return _not_found()

    # Steps 4-5: ask the model to answer from those chunks only.
    system = build_system_prompt(get_settings().company_name)
    text = llm.generate(system, build_user_prompt(question, chunks))

    # Step 6: reject the answer unless every citation is real.
    cited = citations.check_citations(text, len(chunks))
    if cited is None:
        return _not_found()

    return AskResponse(
        answer=citations.renumber(text, cited),
        found=True,
        sources=[_to_source(chunks[number - 1]) for number in cited],
    )


def find_chunks(question: str) -> list[Chunk]:
    """Steps 1b-3: the chunks most likely to answer the question."""
    rewritten = rewrite(question)
    candidates = retrieval.search(question, rewritten)
    if not candidates:
        return []
    # The reranker reads both: the rewrite carries the formal terms, the question its intent.
    return retrieval.rerank(f"{question} {rewritten}", candidates, TOP_K)


def rewrite(question: str) -> str:
    """The question in the documents' formal terms, or the question itself if none came back.

    A one-line rewrite needs no large model: the fast one took 1.5-2 s where the main one
    sometimes stalled for over 10 s.
    """
    reply = llm.generate(REWRITE_PROMPT, build_rewrite_prompt(question), fast=True).strip()
    return reply.splitlines()[0].strip() if reply else question


def _not_found() -> AskResponse:
    return AskResponse(answer=NOT_FOUND, found=False, sources=[])


def _to_source(chunk: Chunk) -> Source:
    return Source(
        document_id=chunk.document_id,
        document_title=chunk.document_title,
        page=chunk.page,
        section_title=chunk.section_title,
        quote=chunk.text,
    )
