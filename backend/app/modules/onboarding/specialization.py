"""The skills of an employee's specialization, from the career module's market data.

Read through the career module's public functions (docs/team.md, "Title skills"), so the
skills, their ids, and their names are the same ones the career gap analysis uses.
"""

from dataclasses import dataclass

from app.modules.career import service as career
from app.modules.career.repository import get_repository

# How many of the title's most requested skills the assessment measures.
TITLE_SKILLS = 6


@dataclass(frozen=True)
class Skill:
    id: int
    key: str
    label_ar: str
    label_en: str


def dictionary() -> dict[str, Skill]:
    """Every skill the platform knows, by key."""
    return {
        row["key"]: Skill(
            row["id"], row["key"], row["label_ar"] or row["label_en"], row["label_en"]
        )
        for row in get_repository().skills.values()
    }


def by_id(skill_id: int) -> Skill:
    row = get_repository().skills[skill_id]
    return Skill(row["id"], row["key"], row["label_ar"] or row["label_en"], row["label_en"])


def title_skills(job_title: str) -> list[Skill]:
    """The skills job postings ask most for this title; none when the title is not in the data."""
    repo = get_repository()
    try:
        title = career.match_title(repo, job_title)
    except career.TitleNotFoundError:
        return []
    ranked = sorted(career.title_skills(repo, title.id), key=lambda skill: -skill.frequency)
    return [by_id(skill.skill_id) for skill in ranked[:TITLE_SKILLS]]


def expected_levels(job_title: str) -> dict[int, int]:
    """The level the title needs per skill, on the career gap analysis's scale."""
    repo = get_repository()
    try:
        title = career.match_title(repo, job_title)
    except career.TitleNotFoundError:
        return {}
    return {
        row.skill_id: career.expected_level(row.frequency, row.required_ratio)
        for row in career.title_skills(repo, title.id)
    }
