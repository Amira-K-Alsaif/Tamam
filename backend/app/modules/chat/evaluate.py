"""Measures the chat on the evaluation questions in data/eval/knowledge_questions.json.

Run from backend/:
    python -m app.modules.chat.evaluate             # retrieval only, no Gemini calls
    python -m app.modules.chat.evaluate --answers   # also asks Gemini (slower, uses quota)

Retrieval is a hit when the expected document is among the chunks the model reads.
An answer is a hit when it is found and contains the expected phrase.
"""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from app.ai.arabic import normalize_arabic

from . import retrieval, service
from .corpus import PROJECT_ROOT

QUESTIONS_FILE = PROJECT_ROOT / "data/eval/knowledge_questions.json"


@dataclass
class Result:
    id: str
    question: str
    expected_document_id: str
    retrieved_document_ids: list[str]
    answer: str | None = None
    answer_hit: bool | None = None

    @property
    def top_hit(self) -> bool:
        return self.retrieved_document_ids[:1] == [self.expected_document_id]

    @property
    def retrieval_hit(self) -> bool:
        return self.expected_document_id in self.retrieved_document_ids


def evaluate(questions: list[dict], with_answers: bool) -> list[Result]:
    results = []
    for item in questions:
        candidates = retrieval.hybrid_search(item["question"])
        chunks = retrieval.rerank(item["question"], candidates, service.TOP_K) if candidates else []
        result = Result(
            id=item["id"],
            question=item["question"],
            expected_document_id=item["expected_document_id"],
            retrieved_document_ids=[chunk.document_id for chunk in chunks],
        )
        if with_answers:
            reply = service.answer(item["question"])
            result.answer = reply.answer
            hint = normalize_arabic(item["expected_answer_hint"])
            result.answer_hit = reply.found and hint in normalize_arabic(reply.answer)
        results.append(result)
    return results


def report(results: list[Result]) -> None:
    total = len(results)

    def share(count: int) -> str:
        return f"{count}/{total} ({count / total:.0%})"

    top_hits = sum(r.top_hit for r in results)
    retrieval_hits = sum(r.retrieval_hit for r in results)
    print(f"Expected document ranked first:  {share(top_hits)}")
    print(f"Expected document in the top {service.TOP_K}:  {share(retrieval_hits)}")
    if results and results[0].answer_hit is not None:
        answer_hits = sum(bool(r.answer_hit) for r in results)
        print(f"Answer found and correct:        {share(answer_hits)}")

    misses = [r for r in results if not r.retrieval_hit or r.answer_hit is False]
    if misses:
        print("\nMisses:")
    for r in misses:
        print(f"- {r.id} {r.question}")
        print(f"    expected {r.expected_document_id}, retrieved {r.retrieved_document_ids}")
        if r.answer is not None:
            print(f"    answer: {r.answer[:120]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the chat on the evaluation set")
    parser.add_argument("--answers", action="store_true", help="also evaluate Gemini's answers")
    parser.add_argument("--questions", type=Path, default=QUESTIONS_FILE)
    args = parser.parse_args()

    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    report(evaluate(questions, with_answers=args.answers))


if __name__ == "__main__":
    main()
