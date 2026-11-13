"""Arabic text normalization shared by every module that searches text.

Documents and questions must be normalized the same way, or matching spellings
such as «إجازة» and «اجازة» would look like different words to the search.
"""

import re
import unicodedata

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
    """Returns the search form of `text`: no diacritics or tatweel, unified letter
    variants, single spaces, and lowercase Latin letters."""
    text = unicodedata.normalize("NFKC", text)
    text = _DIACRITICS.sub("", text).translate(_LETTERS)
    return _SPACES.sub(" ", text).strip().casefold()
