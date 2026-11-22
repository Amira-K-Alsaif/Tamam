from app.modules.career import repository, seed_supabase
from app.modules.career.repository import CareerRepository


class FakeQuery:
    def __init__(self, db, table):
        self.db, self.table, self.start, self.end = db, table, 0, None

    def select(self, _):
        return self

    def range(self, start, end):
        self.start, self.end = start, end
        return self

    def upsert(self, rows):
        self.db.writes.append((self.table, "upsert", rows))
        return self

    def delete(self):
        self.db.writes.append((self.table, "delete", None))
        return self

    def gte(self, *_):
        return self

    def execute(self):
        self.db.requests.append(self.table)
        rows = self.db.rows.get(self.table, [])
        return type("Result", (), {"data": rows[self.start : self.end + 1] if self.end else []})


class FakeSupabase:
    def __init__(self, rows):
        self.rows, self.requests, self.writes = rows, [], []

    def table(self, name):
        return FakeQuery(self, name)


def _json_rows():
    tables = ["job_titles", "skills", "title_skill_profile", "job_postings"]
    return {t: repository._load_json(t) for t in tables}


def test_supabase_source_matches_the_json_files():
    rows = _json_rows()
    # PostgREST returns numeric columns as strings in some setups.
    rows["title_skill_profile"] = [
        {**r, "frequency": str(r["frequency"]), "required_ratio": str(r["required_ratio"])}
        for r in rows["title_skill_profile"]
    ]
    from_db = CareerRepository(FakeSupabase(rows))
    from_json = CareerRepository()
    assert from_db.source == "supabase" and from_json.source == "json"
    assert from_db.titles == from_json.titles
    assert from_db.profiles == from_json.profiles
    assert from_db.postings_count == from_json.postings_count


def test_supabase_reads_every_page():
    db = FakeSupabase({**_json_rows(), "skills": [{"id": i} for i in range(2500)]})
    assert len(CareerRepository(db).skills) == 2500
    assert db.requests.count("skills") == 3


def test_seed_links_titles_after_inserting_them_and_replaces_skill_links():
    db = FakeSupabase({})
    seed_supabase.seed(db)
    title_writes = [rows for table, op, rows in db.writes if table == "job_titles"]
    assert all(t["next_title_id"] is None for t in title_writes[0])
    assert any(t["next_title_id"] for t in title_writes[1])
    ops = [(table, op) for table, op, _ in db.writes]
    assert ops.index(("posting_skills", "delete")) < ops.index(("posting_skills", "upsert"))
    posting = next(rows for table, _, rows in db.writes if table == "job_postings")[0]
    assert set(posting) == set(seed_supabase.POSTING_COLUMNS)
