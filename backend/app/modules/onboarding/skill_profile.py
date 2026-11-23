"""The employee skill profile: the shared contract between onboarding (5) and career (6).

Onboarding writes it from the starting assessment, where the employee rates their level in
each skill of their specialization; career reads it to measure the gap to the next title
from those levels instead of an estimate. Skill ids are the career module's `skills.id`.
See docs/team.md.

Kept in memory until the `employee_skills` table (supabase/migrations) is wired in, so a
server restart resets the demo. An employee's profile is only ever read by their own id.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

Source = Literal["self"]
MAX_LEVEL = 4


@dataclass(frozen=True)
class SkillLevel:
    skill_id: int
    level: int  # 0 (none) to 4 (expert), the scale of the career gap analysis
    source: Source
    updated_at: datetime


_profiles: dict[str, dict[int, SkillLevel]] = {}


def save(employee_id: str, levels: dict[int, int], source: Source = "self") -> None:
    """Records levels for some skills, replacing earlier ones for the same skills."""
    now = datetime.now(UTC)
    profile = _profiles.setdefault(employee_id, {})
    for skill_id, level in levels.items():
        profile[skill_id] = SkillLevel(
            skill_id=skill_id,
            level=max(0, min(level, MAX_LEVEL)),
            source=source,
            updated_at=now,
        )


def profile(employee_id: str) -> dict[int, SkillLevel]:
    return dict(_profiles.get(employee_id, {}))


def levels(employee_id: str) -> dict[int, int] | None:
    """The employee's level per skill, or None when nothing has been recorded yet."""
    rows = _profiles.get(employee_id)
    return {skill_id: row.level for skill_id, row in rows.items()} if rows else None


def clear() -> None:
    """Forgets every profile; for tests and for restarting a demo."""
    _profiles.clear()
