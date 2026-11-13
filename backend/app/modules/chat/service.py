"""Answers an employee's question from the company documents (Retrieval-Augmented
Generation). See README.md in this folder for the full walkthrough."""

from app.ai import llm

from . import citations, retrieval
from .corpus import Chunk
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import AskResponse, Source

# How many chunks the model reads. One is too risky: an answer may need two chunks,
# and the best one is not always ranked first.
TOP_K = 3
NOT_FOUND = "ما لقيت هذي المعلومة في وثائق الشركة."


def answer(question: str) -> AskResponse:
    # Steps 2-3: find the chunks most likely to answer the question.
    candidates = retrieval.hybrid_search(question)
    if not candidates:
        return _not_found()
    chunks = retrieval.rerank(question, candidates, TOP_K)

    # Steps 4-5: ask the model to answer from those chunks only.
    text = llm.generate(SYSTEM_PROMPT, build_user_prompt(question, chunks))

    # Step 6: reject the answer unless every citation is real.
    cited = citations.check_citations(text, len(chunks))
    if cited is None:
        return _not_found()

    return AskResponse(
        answer=citations.renumber(text, cited),
        found=True,
        sources=[_to_source(chunks[number - 1]) for number in cited],
    )


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
