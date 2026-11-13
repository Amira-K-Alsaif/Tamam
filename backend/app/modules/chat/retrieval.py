"""Pipeline steps 2 and 3: find the chunks most likely to answer a question.

question ─┬─► semantic_search  (meaning: «من البيت» finds «عن بعد»)
          └─► keyword_search   (exact words: «VPN» finds «VPN»)
                    │
            hybrid_search      (merges both rankings)
                    │
            rerank             (reorders the shortlist precisely)
"""

from functools import lru_cache

from app.ai import embeddings, reranker

from . import ranking
from .corpus import Chunk, all_chunks

# Low on purpose: the small embedding model scores even unrelated text near 0.8, so the
# reranker, the model, and the citation check do the real filtering. Raise it with BGE-M3.
MIN_SEMANTIC_SCORE = 0.70
# How many chunks the fast searches hand to the slower, more accurate reranker.
CANDIDATES = 10


@lru_cache
def _vectors() -> list[list[float]]:
    """Embeds every chunk once per process."""
    return embeddings.embed_passages([chunk.search_text for chunk in all_chunks()])


@lru_cache
def _keyword_index() -> list[list[str]]:
    """Tokenizes every chunk once per process."""
    return [ranking.tokenize(chunk.search_text) for chunk in all_chunks()]


def warm_up() -> None:
    """Loads both models and builds both indexes now, so the first question is fast."""
    _vectors()
    _keyword_index()
    reranker.warm_up()


def semantic_search(question: str, k: int) -> list[tuple[float, Chunk]]:
    """The `k` chunks closest in meaning to the question, with their cosine similarity."""
    query = embeddings.embed_query(question)
    scored = [
        (sum(a * b for a, b in zip(vector, query, strict=True)), chunk)
        for vector, chunk in zip(_vectors(), all_chunks(), strict=True)
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


def keyword_search(question: str, k: int) -> list[tuple[float, Chunk]]:
    """The `k` chunks that share the most important words with the question."""
    scores = ranking.bm25(ranking.tokenize(question), _keyword_index())
    scored = [
        (score, chunk) for score, chunk in zip(scores, all_chunks(), strict=True) if score > 0
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


def hybrid_search(question: str) -> list[Chunk]:
    """Chunks close in meaning plus chunks sharing exact words, merged by rank."""
    by_meaning = [
        chunk
        for score, chunk in semantic_search(question, CANDIDATES)
        if score >= MIN_SEMANTIC_SCORE
    ]
    by_words = [chunk for _, chunk in keyword_search(question, CANDIDATES)]

    chunks_by_id = {chunk.id: chunk for chunk in by_meaning + by_words}
    merged = ranking.reciprocal_rank_fusion(
        [[chunk.id for chunk in by_meaning], [chunk.id for chunk in by_words]]
    )
    return [chunks_by_id[chunk_id] for chunk_id in merged[:CANDIDATES]]


def rerank(question: str, chunks: list[Chunk], k: int) -> list[Chunk]:
    """The `k` best chunks after the reranker reads each one with the question."""
    scores = reranker.rerank(question, [chunk.search_text for chunk in chunks])
    ranked = sorted(zip(scores, chunks, strict=True), key=lambda pair: pair[0], reverse=True)
    return [chunk for _, chunk in ranked[:k]]
