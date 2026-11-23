"""The starting assessment every employee takes first: their company and their specialization.

- Company: questions on the policies of the employee's department and the company-wide ones,
  from the saved question bank, each proven by a quote from its policy.
- Specialization: for each skill job postings ask most for the employee's title, the employee
  says their level, from «ما أعرفها» to «خبير». The level goes in their skill profile, which
  the career gap analysis reads too.

Nothing here waits on the model, so the assessment opens at once. Grading records the scores
and levels, then the model draws the roadmap. The answer key never leaves the server.
"""

from dataclasses import dataclass

from . import documents, quiz, roadmap_ai, service, skill_profile, specialization
from .schemas import (
    Assessment,
    AssessmentOutcome,
    AssessmentQuestion,
    SkillResult,
    TopicScore,
)

COMPANY_POLICIES = 3
# The answer's position is the level on the career gap analysis's scale (0-4).
LEVELS = ["ما أعرفها", "مبتدئ", "متوسط", "متقدم", "خبير"]


@dataclass(frozen=True)
class _Meta:
    """What a question measures; kept on the server with the answer key."""

    answer: int | None = None  # The right option of a company question
    document_id: str | None = None
    skill_id: int | None = None


# One assessment per employee per server run: the questions and what each one measures.
_assessments: dict[str, tuple[Assessment, list[_Meta]]] = {}


def _company_questions(document_id: str) -> list[tuple[AssessmentQuestion, _Meta]]:
    try:
        questions, key = quiz.assessment_questions(document_id)
    except quiz.QuizUnavailableError:
        # A policy whose questions cannot be traced to its text is left out, not guessed.
        return []
    topic = documents.topic_for(document_id)
    return [
        (
            AssessmentQuestion(
                kind="company",
                topic=topic,
                question=item.question,
                options=item.options,
                source=item.source,
            ),
            _Meta(answer=answer, document_id=document_id),
        )
        for item, answer in zip(questions, key, strict=True)
    ]


def _skill_question(skill: specialization.Skill) -> tuple[AssessmentQuestion, _Meta]:
    question = AssessmentQuestion(
        kind="skill",
        topic=skill.label_ar,
        question=f"وين مستواك في {skill.label_ar}؟",
        options=LEVELS,
        skill_id=skill.id,
    )
    return question, _Meta(skill_id=skill.id)


def get_assessment(employee_id: str) -> Assessment:
    if employee_id not in _assessments:
        employee = service.get_employee(employee_id)
        pairs = [
            pair
            for document_id in documents.policies_for(employee.team, COMPANY_POLICIES)
            for pair in _company_questions(document_id)
        ]
        pairs += [
            _skill_question(skill) for skill in specialization.title_skills(employee.job_title)
        ]
        if not pairs:
            raise quiz.QuizUnavailableError("No usable question")
        _assessments[employee_id] = (
            Assessment(questions=[question for question, _ in pairs]),
            [meta for _, meta in pairs],
        )
    return _assessments[employee_id][0]


def grade_assessment(employee_id: str, answers: list[int]) -> AssessmentOutcome:
    """Scores each policy, records the skill levels, and has the roadmap drawn."""
    if employee_id not in _assessments:
        raise LookupError("Open the assessment before answering it")
    _, metas = _assessments[employee_id]
    if len(answers) != len(metas):
        raise ValueError("One answer per question is required")
    employee = service.get_employee(employee_id)

    correct: list[bool | None] = []
    marks_per_document: dict[str, list[bool]] = {}
    levels: dict[int, int] = {}
    for given, meta in zip(answers, metas, strict=True):
        if meta.skill_id is not None:
            if not 0 <= given < len(LEVELS):
                raise ValueError("A level must be one of the options")
            levels[meta.skill_id] = given
            correct.append(None)
        else:
            is_right = given == meta.answer
            marks_per_document.setdefault(meta.document_id, []).append(is_right)
            correct.append(is_right)

    topics = [
        TopicScore(
            topic=documents.topic_for(doc_id),
            document_id=doc_id,
            score=(score := round(sum(marks) * 100 / len(marks))),
            passed=score >= service.PASSING_SCORE,
        )
        for doc_id, marks in marks_per_document.items()
    ]
    service.record_scores(employee_id, {topic.topic: topic.score for topic in topics})
    skill_profile.save(employee_id, levels)
    service.mark_assessed(employee_id)

    expected = specialization.expected_levels(employee.job_title)
    skills = [
        SkillResult(
            skill_id=skill_id,
            label_ar=specialization.by_id(skill_id).label_ar,
            level=level,
            expected_level=expected.get(skill_id),
        )
        for skill_id, level in levels.items()
    ]
    roadmap_ai.draw(employee, service.knowledge_gaps(employee_id), service.skill_gaps(employee_id))
    return AssessmentOutcome(
        topics=topics,
        skills=skills,
        correct=correct,
        correct_options=[meta.answer for meta in metas],
    )


def clear_assessment() -> None:
    """Forgets generated assessments; for tests."""
    _assessments.clear()
