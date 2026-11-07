"""Turns text into vectors. The only place that loads the embedding model."""

import re
from functools import lru_cache

MODEL_NAME = "intfloat/multilingual-e5-small"


def normalize_arabic(text: str) -> str:
    text = re.sub(r"[\u064B-\u0652\u0640]", "", text)  # diacritics and tatweel
    text = re.sub("[إأآ]", "ا", text)
    return text.replace("ى", "ي")


@lru_cache
def _model():
    # Imported here so the app and its tests start without the heavy library.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_passages(texts: list[str]) -> list[list[float]]:
    prepared = ["passage: " + normalize_arabic(text) for text in texts]
    return _model().encode(prepared, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    prepared = ["query: " + normalize_arabic(text)]
    return _model().encode(prepared, normalize_embeddings=True)[0].tolist()
