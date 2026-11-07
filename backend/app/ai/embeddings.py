"""Turns text into vectors. The only place that loads the embedding model."""

import re
import unicodedata
from functools import lru_cache

MODEL_NAME = "intfloat/multilingual-e5-small"

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_SPACES = re.compile(r"\s+")
_LETTERS = str.maketrans(
    {
        "أ": "ا",  # أ → ا
        "إ": "ا",  # إ → ا
        "آ": "ا",  # آ → ا
        "ٱ": "ا",  # ٱ → ا
        "ى": "ي",  # ى → ي
        "ة": "ه",  # ة → ه
        "ـ": "",  # tatweel
    }
)


def normalize_arabic(text: str) -> str:
    """The one Arabic normalization for documents and questions alike. See CLAUDE.md."""
    text = unicodedata.normalize("NFKC", text)
    text = _DIACRITICS.sub("", text).translate(_LETTERS)
    return _SPACES.sub(" ", text).strip().casefold()


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
