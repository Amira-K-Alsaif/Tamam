"""Arabic script detection for the career module. Normalization is shared in `app.ai.arabic`."""

import re


def has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06ff]", text))
