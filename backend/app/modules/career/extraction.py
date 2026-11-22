"""Skill extraction from job-posting text.

`KeywordExtractor` is the offline baseline: it matches the bilingual skills dictionary.
`LLMExtractor` asks the model through `app/ai/` and returns the same `ExtractedSkill` shape.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.ai import llm
from app.ai.arabic import normalize_arabic as normalize

from .prompts import build_system_prompt, build_user_prompt
from .text_ar import has_arabic

DATA_DIR = Path(__file__).parent / "data"

_PREFERRED_MARKERS = [
    normalize(m)
    for m in ["ميزة", "يفضل", "مفضل", "أفضلية", "preferred", "a plus", "advantage", "nice to have"]
]
_SENTENCE_SPLIT = re.compile(r"[.!؟?؛;•\n]+|(?:\s-\s)")
# Short Arabic aliases (e.g. «قوى», «ساب») must be whole words, or they match «أقوى» and «حساب».
_SHORT_ALIAS_LEN = 4

Importance = Literal["required", "preferred"]


@dataclass(frozen=True)
class ExtractedSkill:
    skill_key: str
    importance: Importance
    method: Literal["keyword", "llm"]
    confidence: float
    source_span: str


def load_dictionary(path: Path | None = None) -> list[dict]:
    path = path or DATA_DIR / "skills_dictionary.json"
    return json.loads(path.read_text(encoding="utf-8"))["skills"]


def _importance(sentence: str) -> Importance:
    return "preferred" if any(m in sentence for m in _PREFERRED_MARKERS) else "required"


def _alternation(words: list[str]) -> str:
    return "|".join(re.escape(w) for w in words)


class KeywordExtractor:
    def __init__(self, dictionary: list[dict]):
        self._rules = []
        for skill in dictionary:
            long_ar, short_ar, en = [], [], []
            for alias in skill["aliases"]:
                n = normalize(alias)
                if not has_arabic(n):
                    en.append(n)
                elif len(n.replace(" ", "")) <= _SHORT_ALIAS_LEN:
                    short_ar.append(n)
                else:
                    long_ar.append(n)
            short_re = (
                re.compile(
                    r"(?<![؀-ۿ])(?:[وفبلك])?(?:ال)?(" + _alternation(short_ar) + r")(?![؀-ۿ])"
                )
                if short_ar
                else None
            )
            en_re = (
                re.compile(r"(?<![a-z0-9])(" + _alternation(en) + r")(?![a-z0-9])") if en else None
            )
            exclude = [normalize(x) for x in skill.get("exclude", [])]
            self._rules.append((skill["key"], long_ar, short_re, en_re, exclude))

    def extract(self, text: str) -> list[ExtractedSkill]:
        sentences = [normalize(s) for s in _SENTENCE_SPLIT.split(text) if s.strip()]
        found: dict[str, ExtractedSkill] = {}
        for key, long_ar, short_re, en_re, exclude in self._rules:
            for sentence in sentences:
                s = sentence
                for phrase in exclude:
                    s = s.replace(phrase, " ")
                hit = (
                    any(a in s for a in long_ar)
                    or (short_re is not None and short_re.search(s))
                    or (en_re is not None and en_re.search(s))
                )
                if not hit:
                    continue
                importance = _importance(sentence)
                previous = found.get(key)
                # A skill listed once as required and once as a plus counts as required.
                if previous is None or (
                    previous.importance == "preferred" and importance == "required"
                ):
                    found[key] = ExtractedSkill(key, importance, "keyword", 0.7, sentence[:300])
        return list(found.values())


class ExtractionError(ValueError):
    """The model's output was not valid JSON or did not match the schema."""


class _LLMSkill(BaseModel):
    key: str
    importance: Importance
    quote: str


class _LLMSkills(BaseModel):
    skills: list[_LLMSkill]


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")
LLM_CONFIDENCE = 0.9


class LLMExtractor:
    """Skills chosen by the model. A skill is kept only when its key is in the dictionary and
    its quote is really in the posting, so the model cannot add a skill the text does not ask for.
    """

    def __init__(self, dictionary: list[dict]):
        self._keys = {s["key"] for s in dictionary}
        self._system = build_system_prompt(dictionary)

    def extract(self, text: str) -> list[ExtractedSkill]:
        raw = llm.generate(self._system, build_user_prompt(text))
        try:
            parsed = _LLMSkills.model_validate(json.loads(_FENCE.sub("", raw.strip())))
        except (json.JSONDecodeError, ValidationError) as error:
            raise ExtractionError(f"Model output is not a valid skill list: {error}") from error
        posting = normalize(text)
        found: dict[str, ExtractedSkill] = {}
        for item in parsed.skills:
            quote = normalize(item.quote)
            if item.key not in self._keys or not quote or quote not in posting:
                continue
            previous = found.get(item.key)
            if previous is None or (
                previous.importance == "preferred" and item.importance == "required"
            ):
                found[item.key] = ExtractedSkill(
                    item.key, item.importance, "llm", LLM_CONFIDENCE, quote[:200]
                )
        return list(found.values())
