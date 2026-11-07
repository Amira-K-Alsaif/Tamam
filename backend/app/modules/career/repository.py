"""Career data access. Reads the generated JSON files until the Supabase tables exist."""

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class CareerRepository:
    def __init__(self) -> None:
        self.titles: dict[int, dict] = {t["id"]: t for t in _load("job_titles.json")}
        self.skills: dict[int, dict] = {s["id"]: s for s in _load("skills.json")}
        self.profiles: dict[int, list[dict]] = {}
        for row in _load("title_skill_profile.json"):
            self.profiles.setdefault(row["job_title_id"], []).append(row)
        self.postings_count = Counter(p["job_title_id"] for p in _load("job_postings.json"))


@lru_cache
def get_repository() -> CareerRepository:
    return CareerRepository()
