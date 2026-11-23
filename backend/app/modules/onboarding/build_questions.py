"""Builds the policy question bank the assessment and the lesson quizzes read from.

The model writes the questions from each company policy, once, and each is kept only when its
quote is really in the policy (quiz.parse_questions). Saving them means the assessment opens
instantly instead of waiting on the model. Run again whenever the policies change:

    python -m app.modules.onboarding.build_questions
"""

import json
from concurrent.futures import ThreadPoolExecutor

from . import documents, quiz

# The first questions go in the starting assessment, the rest in the lesson quiz.
QUESTIONS_PER_POLICY = 5


def build() -> dict[str, int]:
    policies = [doc_id for doc_id, _ in documents.policies()]

    def generate(doc_id: str):
        questions, key = quiz.generate_questions(doc_id, QUESTIONS_PER_POLICY)
        return doc_id, [
            {**question.model_dump(), "answer": answer}
            for question, answer in zip(questions, key, strict=True)
        ]

    with ThreadPoolExecutor(max_workers=len(policies)) as pool:
        bank = dict(pool.map(generate, policies))
    documents.QUESTION_BANK.write_text(
        json.dumps(bank, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return {doc_id: len(questions) for doc_id, questions in bank.items()}


if __name__ == "__main__":
    for doc_id, count in build().items():
        print(f"{doc_id}: {count} questions")
