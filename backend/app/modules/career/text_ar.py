"""Arabic normalization so forms like «إدارة» and «ادارة» match as the same word."""

import re

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
_TATWEEL = "ـ"


def normalize(text: str) -> str:
    if not text:
        return ""
    t = _DIACRITICS.sub("", text).replace(_TATWEEL, "")
    t = re.sub("[إأآٱ]", "ا", t)
    t = t.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub(r"\s+", " ", t.lower()).strip()


def has_arabic(text: str) -> bool:
    return bool(re.search(r"[؀-ۿ]", text))
