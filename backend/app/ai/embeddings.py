"""Turns text into vectors that capture its meaning. The only place that loads the
embedding model."""

from functools import lru_cache

from app.ai.arabic import normalize_arabic

MODEL_NAME = "intfloat/multilingual-e5-small"


@lru_cache
def _model():
    # Imported here so the app and its tests start without the heavy library.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embeds document chunks. Vectors are unit length, so a dot product is the cosine
    similarity."""
    # e5 models are trained with these prefixes and lose accuracy without them.
    prepared = ["passage: " + normalize_arabic(text) for text in texts]
    return _model().encode(prepared, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    """Embeds a user question in the same space as `embed_passages`."""
    prepared = ["query: " + normalize_arabic(text)]
    return _model().encode(prepared, normalize_embeddings=True)[0].tolist()
