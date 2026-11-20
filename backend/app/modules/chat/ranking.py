"""Ranking algorithms used by retrieval: keyword scoring (BM25) and rank fusion.

Plain Python with no model, so they are fast and easy to test.
"""

import math
import re
from collections import Counter

from app.ai.arabic import normalize_arabic

# Words so common they match almost every chunk. Written in their normalized form.
STOP_WORDS = {
    "من", "في", "علي", "عن", "الي", "او", "و", "ان", "ما", "هل", "كم", "كيف", "متي",
    "مين", "وش", "ايش", "ابي", "ابغي", "لي", "لا", "مع", "بعد", "قبل", "هذا", "هذي", "هذه",
    "اي", "كل", "عند", "انا", "يا",
}  # fmt: skip


def tokenize(text: str) -> list[str]:
    """Splits text into search words: normalized, without «ال», and without stop words."""
    words = re.findall(r"\w+", normalize_arabic(text))
    # Drop the definite article so «الإجازة» matches «إجازة». Short words keep it,
    # because in them «ال» is usually part of the word itself.
    words = [word[2:] if word.startswith("ال") and len(word) > 4 else word for word in words]
    return [word for word in words if word not in STOP_WORDS]


def bm25(
    query: list[str], documents: list[list[str]], k1: float = 1.5, b: float = 0.75
) -> list[float]:
    """Scores each document by how often it uses the query's words.

    Rare words count more than common ones, repeated words count less each time
    (`k1`), and long documents are not rewarded just for being long (`b`).
    """
    count = len(documents)
    average_length = sum(len(document) for document in documents) / count
    document_frequency = Counter(word for document in documents for word in set(document))

    scores = []
    for document in documents:
        frequency = Counter(document)
        length_penalty = 1 - b + b * len(document) / average_length
        score = 0.0
        for word in query:
            if word not in frequency:
                continue
            rarity = math.log(
                1 + (count - document_frequency[word] + 0.5) / (document_frequency[word] + 0.5)
            )
            score += rarity * frequency[word] * (k1 + 1) / (frequency[word] + k1 * length_penalty)
        scores.append(score)
    return scores


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    """Merges several rankings of ids into one.

    Uses each id's position rather than its score, because scores from different
    searches are on different scales. An id ranked high in any list rises to the top.
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1 / (k + rank)
    return sorted(scores, key=lambda item: scores[item], reverse=True)
