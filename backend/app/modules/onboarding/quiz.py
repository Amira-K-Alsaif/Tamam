"""Lesson quizzes: generated from the lesson's policy document, graded on the server.

The answer key never leaves the server: `get_quiz` returns the questions only, and
`grade_quiz` checks the answers against the key kept here. Each passing or failing score is
recorded, so the roadmap reorders as quizzes are retaken.
"""

import json
import re

from pydantic import BaseModel, Field, ValidationError

from app.ai import llm
from app.ai.arabic import normalize_arabic

from . import documents, prompts, service
from .documents import load_document, topic_for
from .schemas import Quiz, QuizQuestion, QuizResult, SourceCitation

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


class QuizUnavailableError(RuntimeError):
    """The model is not configured, did not answer, or wrote no usable question."""


class _LLMQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=2, max_length=4)
    answer: int
    section_title: str
    quote: str


class _LLMQuiz(BaseModel):
    questions: list[_LLMQuestion]


# One quiz per document per server run, with its answer key: (quiz, correct option per question).
_quizzes: dict[str, tuple[Quiz, list[int]]] = {}


def _comparable(text: str) -> str:
    return " ".join(normalize_arabic(text).split())


def parse_questions(
    raw: str, document_id: str, title: str, markdown: str
) -> tuple[list[QuizQuestion], list[int]]:
    """Keeps only questions whose answer index is valid and whose quote is really in the text."""
    try:
        parsed = _LLMQuiz.model_validate(json.loads(_FENCE.sub("", raw.strip())))
    except (json.JSONDecodeError, ValidationError) as error:
        raise QuizUnavailableError("The model did not return a quiz") from error

    text = _comparable(markdown)
    questions: list[QuizQuestion] = []
    key: list[int] = []
    for item in parsed.questions:
        if not 0 <= item.answer < len(item.options):
            continue
        if _comparable(item.quote) not in text:
            continue
        questions.append(
            QuizQuestion(
                question=item.question,
                options=item.options,
                source=SourceCitation(
                    document_id=document_id,
                    document_title=title,
                    page=None,
                    section_title=item.section_title.lstrip("# ").strip(),
                    quote=item.quote,
                ),
            )
        )
        key.append(item.answer)
    if not questions:
        raise QuizUnavailableError("No question could be traced to the document")
    return questions, key


def generate_questions(document_id: str, count: int) -> tuple[list[QuizQuestion], list[int]]:
    """Asks the model for `count` questions on the document, keeping only traceable ones."""
    title, markdown = load_document(document_id)
    try:
        raw = llm.generate(prompts.build_system(count), prompts.build_user_prompt(title, markdown))
    except (llm.LLMNotConfiguredError, llm.LLMUnavailableError) as error:
        raise QuizUnavailableError(str(error)) from error
    return parse_questions(raw, document_id, title, markdown)


# The first saved questions of a policy go in the starting assessment, the rest in its lesson.
ASSESSMENT_QUESTIONS = 2


def _saved(document_id: str) -> tuple[list[QuizQuestion], list[int]]:
    rows = documents.bank().get(document_id, [])
    questions = [QuizQuestion(**{k: v for k, v in row.items() if k != "answer"}) for row in rows]
    return questions, [row["answer"] for row in rows]


def assessment_questions(document_id: str) -> tuple[list[QuizQuestion], list[int]]:
    """From the saved bank, so the assessment opens at once; generated if the bank lacks it."""
    questions, key = _saved(document_id)
    if len(questions) >= ASSESSMENT_QUESTIONS:
        return questions[:ASSESSMENT_QUESTIONS], key[:ASSESSMENT_QUESTIONS]
    return generate_questions(document_id, ASSESSMENT_QUESTIONS)


def lesson_questions(document_id: str) -> tuple[list[QuizQuestion], list[int]]:
    """Saved questions the assessment did not ask, or new ones if none are left."""
    questions, key = _saved(document_id)
    if len(questions) > ASSESSMENT_QUESTIONS:
        return questions[ASSESSMENT_QUESTIONS:], key[ASSESSMENT_QUESTIONS:]
    return generate_questions(document_id, prompts.QUESTION_COUNT)


def get_quiz(document_id: str) -> Quiz:
    """The lesson's quiz on its policy, kept for this server run."""
    topic = topic_for(document_id)
    if document_id not in _quizzes:
        questions, key = lesson_questions(document_id)
        quiz = Quiz(
            topic=topic,
            document_id=document_id,
            document_title=questions[0].source.document_title,
            questions=questions,
        )
        _quizzes[document_id] = (quiz, key)
    return _quizzes[document_id][0]


def grade_quiz(employee_id: str, document_id: str, answers: list[int]) -> QuizResult:
    """Scores the answers, records the score, and says which options were right."""
    topic = topic_for(document_id)
    if document_id not in _quizzes:
        raise LookupError("Open the quiz before answering it")
    _, key = _quizzes[document_id]
    if len(answers) != len(key):
        raise ValueError("One answer per question is required")

    correct = [given == right for given, right in zip(answers, key, strict=True)]
    score = round(sum(correct) * 100 / len(key))
    service.record_quiz_score(employee_id, topic, score)
    return QuizResult(
        topic=topic,
        score=score,
        passed=score >= service.PASSING_SCORE,
        correct=correct,
        correct_options=key,
    )


def clear_quizzes() -> None:
    """Forgets generated quizzes; for tests."""
    _quizzes.clear()
