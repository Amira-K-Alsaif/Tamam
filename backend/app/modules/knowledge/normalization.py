"""Use the same Arabic normalization for ingestion and search queries."""

import re
import unicodedata

_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
_SPACES = re.compile(r"\s+")
_TRANSLATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ـ": "",
    }
)


def normalize_arabic(text: str) -> str:
    """Create a search representation while preserving original text for citations."""
    text = unicodedata.normalize("NFKC", text)
    text = _DIACRITICS.sub("", text).translate(_TRANSLATION)
    return _SPACES.sub(" ", text).strip().casefold()
