"""Explainable policy review candidates and non-destructive data quality checks.

This module NEVER labels a mismatch as a confirmed contradiction. It flags
numeric thresholds in similarly worded passages for a human reviewer.
"""

import re
from itertools import combinations
from typing import Any

from app.ai.arabic import normalize_arabic

_WORDS = {
    "واحد": 1,
    "واحده": 1,
    "اثنان": 2,
    "اثنين": 2,
    "اثنتان": 2,
    "ثلاثه": 3,
    "اربعه": 4,
    "خمسه": 5,
    "سته": 6,
    "سبعه": 7,
    "ثمانيه": 8,
    "تسعه": 9,
    "عشر": 10,
    "عشره": 10,
    "احد": 1,
    "اثنا": 2,
    "اثني": 2,
}
_UNITS = {
    "يوم": "day",
    "يوما": "day",
    "ايام": "day",
    "ساعه": "hour",
    "ساعات": "hour",
    "شهر": "month",
    "اشهر": "month",
    "شهور": "month",
    "دقيقه": "minute",
    "دقائق": "minute",
}
_STOPWORDS = {
    "و",
    "او",
    "من",
    "في",
    "على",
    "عن",
    "الى",
    "ان",
    "اذا",
    "هذه",
    "هذا",
    "ذلك",
    "يتم",
    "هو",
    "هي",
    "مع",
    "تم",
    "كل",
    "ما",
    "عند",
    "ال",
}
# All input is normalized by the shared app.ai.arabic implementation.
_UNITS_RE = "|".join(sorted(_UNITS, key=len, reverse=True))
_WORDS_RE = "|".join(sorted(_WORDS, key=len, reverse=True))
_QUANTITY = re.compile(rf"(?<!\w)ب?(\d+|(?:{_WORDS_RE})(?:\s+(?:عشر|عشره))?)\s+({_UNITS_RE})(?!\w)")
_SENTENCES = re.compile(r"[\n.!؟؛]+")
_WORD = re.compile(r"[\w]+", re.UNICODE)


def _number(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    parts = value.split()
    if len(parts) == 2 and parts[1] in ("عشر", "عشره") and parts[0] in _WORDS:
        return 10 + _WORDS[parts[0]]
    return _WORDS.get(value)


def _quantities(text: str) -> list[tuple[int, str]]:
    normalized = normalize_arabic(text)
    # ٠١٢... and ۰۱۲... -> ASCII, while keeping other characters unchanged.
    digit_map = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
    normalized = normalized.translate(digit_map)
    results: list[tuple[int, str]] = []
    for match in _QUANTITY.finditer(normalized):
        value = _number(match.group(1))
        if value is not None:
            results.append((value, _UNITS[match.group(2)]))
    return results


def _anchors(sentence: str) -> set[str]:
    cleaned = _QUANTITY.sub(" ", normalize_arabic(sentence))
    tokens = set(_WORD.findall(cleaned))
    return {x for x in tokens if x not in _STOPWORDS and len(x) > 2}


def _passages(documents: list[dict[str, Any]], chunks: list[dict[str, Any]]):
    index = {str(d["id"]): d for d in documents if d.get("id")}
    for chunk in chunks:
        document = index.get(str(chunk.get("document_id", "")))
        if not document or document.get("status") != "ready":
            continue
        # Do not compare against archived/processing/deleted content.
        for sentence in _SENTENCES.split(str(chunk.get("text") or "")):
            sentence = sentence.strip()
            quantity = _quantities(sentence)
            # Ambiguous multi-threshold statements (e.g. 21 vs 30 after 5 years)
            # are deliberately excluded from the first-pass comparison.
            if len(quantity) != 1:
                continue
            value, unit = quantity[0]
            yield {
                "document_id": str(document["id"]),
                "document_title": str(document.get("title") or ""),
                "department": str(document.get("department") or ""),
                "section_title": str(chunk.get("section_title") or ""),
                "chunk_id": str(chunk.get("id") or ""),
                "quote": sentence,
                "value": value,
                "unit": unit,
                "anchors": _anchors(sentence),
            }


def find_policy_conflicts(
    documents: list[dict[str, Any]], chunks: list[dict[str, Any]], limit: int = 50
) -> list[dict[str, Any]]:
    """Return cited *candidates*, not asserted legal or semantic contradictions.

    A candidate needs distinct documents, same department, different numeric
    value in the same unit, and strongly overlapping substantive wording.
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    passages = list(_passages(documents, chunks))
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for a, b in combinations(passages, 2):
        if a["document_id"] == b["document_id"]:
            continue
        if a["department"] != b["department"] or a["unit"] != b["unit"]:
            continue
        if a["value"] == b["value"]:
            continue
        shared = a["anchors"] & b["anchors"]
        union = a["anchors"] | b["anchors"]
        if len(shared) < 4 or not union or len(shared) / len(union) < 0.65:
            continue
        identity = tuple(sorted((a["chunk_id"], b["chunk_id"]))) + (
            a["unit"],
            str(min(a["value"], b["value"])),
        )
        if identity in seen:
            continue
        seen.add(identity)
        sources = [
            {
                key: part[key]
                for key in ("document_id", "document_title", "section_title", "chunk_id", "quote")
            }
            for part in (a, b)
        ]
        found.append(
            {
                "status": "needs_review",
                "reason": "different_numeric_thresholds_in_similar_text",
                "unit": a["unit"],
                "values": [a["value"], b["value"]],
                "sources": sources,
            }
        )
        if len(found) == limit:
            break
    return found


def audit_knowledge_data(
    documents: list[dict[str, Any]], chunks: list[dict[str, Any]], limit: int = 100
) -> dict[str, Any]:
    """Report data quality issues without deleting or modifying database rows."""
    valid_ids = {str(d.get("id")) for d in documents}
    issues: list[dict[str, str]] = []
    seen: dict[tuple[str, str], str] = {}
    for doc in documents:
        if not str(doc.get("title") or "").strip():
            issues.append({"type": "missing_document_title", "document_id": str(doc.get("id"))})
    for chunk in chunks:
        cid = str(chunk.get("id") or "")
        did = str(chunk.get("document_id") or "")
        text = str(chunk.get("text") or "")
        normalized = normalize_arabic(text)
        if did not in valid_ids:
            issues.append({"type": "orphan_chunk", "chunk_id": cid, "document_id": did})
        if not normalized:
            issues.append({"type": "empty_chunk", "chunk_id": cid})
        elif (did, normalized) in seen:
            issues.append(
                {"type": "duplicate_chunk", "chunk_id": cid, "original_id": seen[(did, normalized)]}
            )
        else:
            seen[(did, normalized)] = cid
        if not str(chunk.get("section_title") or "").strip():
            issues.append({"type": "missing_section_title", "chunk_id": cid})
    return {
        "documents_count": len(documents),
        "chunks_count": len(chunks),
        "issues_count": len(issues),
        "issues": issues[:limit],
        "truncated": len(issues) > limit,
        "mode": "read_only",
    }
