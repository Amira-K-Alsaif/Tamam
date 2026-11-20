"""Career data access.

Reads the Supabase career tables when SUPABASE_URL and SUPABASE_SECRET_KEY are set, and the
generated JSON files in data/ otherwise (tests, and local work before the database is seeded).
The JSON files are also what `seed_supabase` uploads, so both sources hold the same rows.
"""

import json
import os
from collections import Counter
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
PAGE_SIZE = 1000  # Supabase returns at most 1000 rows per request.


@lru_cache
def get_supabase():
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    if not url or not key:
        return None
    from supabase import create_client

    return create_client(url, key)


def _load_json(table: str) -> list[dict]:
    return json.loads((DATA_DIR / f"{table}.json").read_text(encoding="utf-8"))


def _load_supabase(db, table: str) -> list[dict]:
    rows: list[dict] = []
    while True:
        page = db.table(table).select("*").range(len(rows), len(rows) + PAGE_SIZE - 1).execute()
        rows += page.data
        if len(page.data) < PAGE_SIZE:
            return rows


class CareerRepository:
    def __init__(self, db=None) -> None:
        self.source = "supabase" if db is not None else "json"

        def load(table: str) -> list[dict]:
            return _load_supabase(db, table) if db is not None else _load_json(table)

        self.titles: dict[int, dict] = {t["id"]: t for t in load("job_titles")}
        self.skills: dict[int, dict] = {s["id"]: s for s in load("skills")}
        self.profiles: dict[int, list[dict]] = {}
        for row in load("title_skill_profile"):
            row = {
                **row,
                "frequency": float(row["frequency"]),
                "required_ratio": float(row["required_ratio"]),
            }
            self.profiles.setdefault(row["job_title_id"], []).append(row)
        self.postings_count = Counter(p["job_title_id"] for p in load("job_postings"))


@lru_cache
def get_repository() -> CareerRepository:
    return CareerRepository(get_supabase())
