"""The starting assessment every employee takes first: their company and their specialization.

- Company: the model picks the policies that matter most for the employee's role, then writes
  questions from each one. A question is kept only when its quote is really in the policy.
- Specialization: two questions (basic and advanced) per skill, for the skills job postings
  ask most for the employee's title plus the ones their CV shows. These come from the model's
  general knowledge of the skill, not from a company document, so they carry no source.

Grading records a score per policy and a level per skill, then the model draws the roadmap.
The answer key never leaves the server.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.ai import llm

from . import documents, prompts, quiz, roadmap_ai, service, skill_profile, specialization
from .schemas import (
    Assessment,
    AssessmentOutcome,
    AssessmentQuestion,
    EmployeeProfile,
    SkillResult,
    TopicScore,
)

COMPANY_DOCUMENTS = 3
QUESTIONS_PER_DOCUMENT = 2
# The title's top skills plus up to this many more from the CV.
EXTRA_CV_SKILLS = 2

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")

SkillQuestionLevel = Literal["basic", "advanced"]


@dataclass(frozen=True)
class _Meta:
    """What a question measures; kept on the server with the answer key."""

    answer: int
    document_id: str | None = None
    skill_id: int | None = None
    level: SkillQuestionLevel | None = None


# One assessment per employee per server run: the questions and what each one measures.
_assessments: dict[str, tuple[Assessment, list[_Meta]]] = {}


class _Picked(BaseModel):
    document_ids: list[str]


class _LLMSkillQuestion(BaseModel):
    skill: str
    level: SkillQuestionLevel
    question: str
    options: list[str] = Field(min_length=2, max_length=4)
    answer: int


class _LLMSkillQuestions(BaseModel):
    questions: list[_LLMSkillQuestion]


def _ask(system: str, user: str) -> str:
    try:
        return _FENCE.sub("", llm.generate(system, user).strip())
    except (llm.LLMNotConfiguredError, llm.LLMUnavailableError) as error:
        raise quiz.QuizUnavailableError(str(error)) from error


def _profile(employee: EmployeeProfile) -> dict:
    return {"job_title": employee.job_title, "team": employee.team}


def pick_documents(employee: EmployeeProfile) -> list[str]:
    """The policies this employee should be assessed on, chosen by the model from the real ones."""
    policies = documents.policies()
    system = prompts.PICK_DOCUMENTS_SYSTEM.format(count=COMPANY_DOCUMENTS)
    raw = _ask(system, prompts.build_pick_documents_prompt(_profile(employee), policies))
    try:
        picked = _Picked.model_validate(json.loads(raw)).document_ids
    except (json.JSONDecodeError, ValidationError) as error:
        raise quiz.QuizUnavailableError("The model did not pick any policy") from error
    known = {doc_id for doc_id, _ in policies}
    chosen = list(dict.fromkeys(doc_id for doc_id in picked if doc_id in known))
    if not chosen:
        raise quiz.QuizUnavailableError("The model picked no known policy")
    return chosen[:COMPANY_DOCUMENTS]


def skills_to_measure(employee: EmployeeProfile) -> list[specialization.Skill]:
    """The title's most requested skills, then skills the CV shows that the title does not list."""
    skills = specialization.title_skills(employee.job_title)
    listed = {skill.id for skill in skills}
    from_cv = [
        specialization.by_id(row.skill_id)
        for row in skill_profile.profile(employee.id).values()
        if row.source == "cv" and row.skill_id not in listed
    ]
    return skills + from_cv[:EXTRA_CV_SKILLS]


def skill_questions(
    skills: list[specialization.Skill],
) -> list[tuple[AssessmentQuestion, _Meta]]:
    """A basic and an advanced question per skill, in the order the skills were given."""
    if not skills:
        return []
    raw = _ask(
        prompts.SKILL_QUESTIONS_SYSTEM,
        prompts.build_skill_questions_prompt([(skill.key, skill.label_ar) for skill in skills]),
    )
    try:
        parsed = _LLMSkillQuestions.model_validate(json.loads(raw)).questions
    except (json.JSONDecodeError, ValidationError) as error:
        raise quiz.QuizUnavailableError("The model did not return skill questions") from error

    chosen: dict[tuple[str, str], _LLMSkillQuestion] = {}
    for item in parsed:
        if 0 <= item.answer < len(item.options):
            chosen.setdefault((item.skill, item.level), item)
    questions = []
    for skill in skills:
        for level in ("basic", "advanced"):
            item = chosen.get((skill.key, level))
            if item is None:
                continue
            question = AssessmentQuestion(
                kind="skill",
                topic=skill.label_ar,
                question=item.question,
                options=item.options,
                skill_id=skill.id,
            )
            questions.append((question, _Meta(answer=item.answer, skill_id=skill.id, level=level)))
    return questions


def _company_questions(document_id: str) -> list[tuple[AssessmentQuestion, _Meta]]:
    try:
        generated, key = quiz.generate_questions(document_id, QUESTIONS_PER_DOCUMENT)
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
        for item, answer in list(zip(generated, key, strict=True))[:QUESTIONS_PER_DOCUMENT]
    ]


def get_assessment(employee_id: str) -> Assessment:
    """Generates the employee's assessment once; the policies and skills are asked at once."""
    if employee_id not in _assessments:
        employee = service.get_employee(employee_id)
        documents = pick_documents(employee)
        skills = skills_to_measure(employee)
        with ThreadPoolExecutor(max_workers=len(documents) + 1) as pool:
            specialty_job = pool.submit(skill_questions, skills)
            company = list(pool.map(_company_questions, documents))
            specialty = specialty_job.result()

        pairs = [pair for questions in company for pair in questions] + specialty
        if not pairs:
            raise quiz.QuizUnavailableError("No usable question was generated")
        _assessments[employee_id] = (
            Assessment(questions=[question for question, _ in pairs]),
            [meta for _, meta in pairs],
        )
    return _assessments[employee_id][0]


def skill_level(basic: bool | None, advanced: bool | None, in_cv: bool) -> int:
    """Two answers to a level on the career scale (0-4). A CV mention alone counts as 1."""
    if basic and advanced:
        return 4
    if advanced:
        return 3
    if basic:
        return 2
    return 1 if in_cv else 0


def grade_assessment(employee_id: str, answers: list[int]) -> AssessmentOutcome:
    """Scores each policy, levels each skill, records both, and has the roadmap drawn."""
    if employee_id not in _assessments:
        raise LookupError("Open the assessment before answering it")
    _, metas = _assessments[employee_id]
    if len(answers) != len(metas):
        raise ValueError("One answer per question is required")
    employee = service.get_employee(employee_id)
    correct = [given == meta.answer for given, meta in zip(answers, metas, strict=True)]

    marks_per_document: dict[str, list[bool]] = {}
    marks_per_skill: dict[int, dict[str, bool]] = {}
    for meta, is_right in zip(metas, correct, strict=True):
        if meta.document_id:
            marks_per_document.setdefault(meta.document_id, []).append(is_right)
        elif meta.skill_id is not None and meta.level:
            marks_per_skill.setdefault(meta.skill_id, {})[meta.level] = is_right

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

    cv_skills = {
        row.skill_id for row in skill_profile.profile(employee_id).values() if row.source == "cv"
    }
    levels = {
        skill_id: skill_level(marks.get("basic"), marks.get("advanced"), skill_id in cv_skills)
        for skill_id, marks in marks_per_skill.items()
    }
    skill_profile.save(
        employee_id,
        levels,
        source="assessment",
        evidence={
            skill_id: f"{sum(marks.values())} من {len(marks)} في التقييم الأولي"
            for skill_id, marks in marks_per_skill.items()
        },
    )
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
