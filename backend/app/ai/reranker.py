"""Reorders retrieved chunks by reading each one together with the question."""

from functools import lru_cache

from app.ai.embeddings import normalize_arabic

MODEL_NAME = "BAAI/bge-reranker-v2-m3"


@lru_cache
def _model():
    # Imported here so the app and its tests start without the heavy library.
    from sentence_transformers import CrossEncoder

    return CrossEncoder(MODEL_NAME)


def rerank(question: str, texts: list[str]) -> list[float]:
    pairs = [(normalize_arabic(question), normalize_arabic(text)) for text in texts]
    return _model().predict(pairs).tolist()
