"""Career rules: title skill profiles and the gap between a current and a target title.

Readiness is a weighted average: a skill's weight is the share of target-title postings
that ask for it, so the skills the market asks for most count most.
"""

from .repository import CareerRepository
from .schemas import Gap, GapAnalysis, GapSkill, JobTitle, MissingSkill, TitleSkill

MIN_FREQUENCY = 0.15
RADAR_AXES = 8


class TitleNotFoundError(LookupError):
    pass


def expected_level(frequency: float, required_ratio: float) -> int:
    return 4 if frequency >= 0.3 and required_ratio >= 0.5 else 3


def proxy_level(frequency: float | None) -> int:
    """Estimate an employee's level from how common the skill is in their current title."""
    if not frequency:
        return 0
    if frequency >= 0.5:
        return 4
    if frequency >= 0.3:
        return 3
    if frequency >= MIN_FREQUENCY:
        return 2
    return 1


def priority(frequency: float) -> str:
    return "high" if frequency >= 0.5 else "medium" if frequency >= 0.3 else "low"


def list_titles(repo: CareerRepository) -> list[JobTitle]:
    return [
        JobTitle(**t, postings_count=repo.postings_count.get(t["id"], 0))
        for t in repo.titles.values()
    ]


def title_skills(repo: CareerRepository, title_id: int) -> list[TitleSkill]:
    if title_id not in repo.titles:
        raise TitleNotFoundError(title_id)
    out = []
    for row in repo.profiles.get(title_id, []):
        s = repo.skills[row["skill_id"]]
        out.append(
            TitleSkill(
                skill_id=s["id"],
                esco_id=s["esco_id"],
                label_ar=s["label_ar"],
                label_en=s["label_en"],
                category=s["category"],
                frequency=row["frequency"],
                required_ratio=row["required_ratio"],
                postings_count=row["postings_count"],
            )
        )
    return out


def analyze_gap(
    repo: CareerRepository,
    current_title_id: int,
    target_title_id: int,
    employee_skills: dict[int, int] | None = None,
) -> GapAnalysis:
    for title_id in (current_title_id, target_title_id):
        if title_id not in repo.titles:
            raise TitleNotFoundError(title_id)

    current_freq = {r["skill_id"]: r["frequency"] for r in repo.profiles.get(current_title_id, [])}
    target = sorted(repo.profiles.get(target_title_id, []), key=lambda r: -r["frequency"])
    considered = [r for r in target if r["frequency"] >= MIN_FREQUENCY] or target[:RADAR_AXES]

    matched: list[GapSkill] = []
    missing: list[MissingSkill] = []
    to_improve: list[GapSkill] = []
    weighted = total = 0.0
    for row in considered:
        skill = repo.skills[row["skill_id"]]
        freq = row["frequency"]
        exp = expected_level(freq, row["required_ratio"])
        if employee_skills is None:
            level = proxy_level(current_freq.get(row["skill_id"]))
        else:
            level = employee_skills.get(row["skill_id"], 0)
        item = GapSkill(
            skill_id=skill["id"],
            label_ar=skill["label_ar"],
            label_en=skill["label_en"],
            market_frequency=freq,
            expected_level=exp,
            employee_level=level,
        )
        if level >= exp:
            matched.append(item)
        elif level == 0:
            missing.append(MissingSkill(**item.model_dump(), priority=priority(freq)))
        else:
            to_improve.append(item)
        weighted += freq * min(level / exp, 1.0)
        total += freq

    radar = [*matched, *to_improve, *missing]
    radar.sort(key=lambda s: -s.market_frequency)
    return GapAnalysis(
        current_title_id=current_title_id,
        target_title_id=target_title_id,
        readiness_score=round(100 * weighted / total, 1) if total else 0.0,
        level_source="current_title_market_proxy"
        if employee_skills is None
        else "employee_profile",
        gap=Gap(
            matched=matched,
            missing=missing,
            to_improve=to_improve,
            evidence_postings=repo.postings_count.get(target_title_id, 0),
        ),
        radar=[
            GapSkill(**s.model_dump(include=set(GapSkill.model_fields))) for s in radar[:RADAR_AXES]
        ],
    )
