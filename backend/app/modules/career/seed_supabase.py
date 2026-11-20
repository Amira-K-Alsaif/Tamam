"""Upload the generated career data files to Supabase.

Run after applying supabase/migrations/20261121_career.sql, and again after rebuilding the data:

    cd backend && python -m app.modules.career.seed_supabase
"""

import json

from .repository import DATA_DIR, get_supabase

BATCH = 500
POSTING_COLUMNS = ("id", "posting_code", "job_title_id")


def _load(name: str) -> list[dict]:
    return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _upsert(db, table: str, rows: list[dict]) -> None:
    for i in range(0, len(rows), BATCH):
        db.table(table).upsert(rows[i : i + BATCH]).execute()
    print(f"{table}: {len(rows)}")


def seed(db) -> None:
    titles = _load("job_titles")
    # next_title_id points at other titles, so insert every title before linking them.
    _upsert(db, "job_titles", [{**t, "next_title_id": None} for t in titles])
    _upsert(db, "job_titles", titles)
    _upsert(db, "skills", _load("skills"))
    postings = [{k: p.get(k) for k in POSTING_COLUMNS} for p in _load("job_postings")]
    _upsert(db, "job_postings", postings)
    # Replace the links so a re-extraction does not mix old and new skills.
    db.table("posting_skills").delete().gte("posting_id", 0).execute()
    _upsert(db, "posting_skills", _load("posting_skills"))


if __name__ == "__main__":
    db = get_supabase()
    if db is None:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SECRET_KEY in backend/.env first.")
    seed(db)
