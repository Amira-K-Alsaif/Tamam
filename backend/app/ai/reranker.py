"""Scores how well each text answers a question by reading the two together.

More accurate than comparing embeddings, but too slow to run on every chunk, so it
only reorders the shortlist that the fast search returns.
"""

from functools import lru_cache

from app.ai.arabic import normalize_arabic

MODEL_NAME = "BAAI/bge-reranker-v2-m3"


@lru_cache
def _model():
    # Imported here so the app and its tests start without the heavy library.
    from sentence_transformers import CrossEncoder

    return CrossEncoder(MODEL_NAME)


def warm_up() -> None:
    """Loads the model now instead of on the first call."""
    _model()


def rerank(question: str, texts: list[str]) -> list[float]:
    """Returns one relevance score per text, in the same order as `texts`."""
    pairs = [(normalize_arabic(question), normalize_arabic(text)) for text in texts]
    return _model().predict(pairs).tolist()
