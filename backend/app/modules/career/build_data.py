"""Rebuild the career data files from the collected job postings.

cd backend && python -m app.modules.career.build_data
"""

import csv
import json
from collections import Counter
from pathlib import Path

from .extraction import DATA_DIR, KeywordExtractor, load_dictionary
from .profiles import build_title_profiles

SOURCE_DIR = Path(__file__).resolve().parents[4] / "data" / "career"


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _titles() -> list[dict]:
    rows = _read_csv(SOURCE_DIR / "job_titles.csv")
    id_of = {r["code"]: int(float(r["id"])) for r in rows}
    return [
        {
            "id": int(float(r["id"])),
            "code": r["code"],
            "ladder": r["ladder_en"],
            "level": r["level_en"],
            "name_ar": r["name_ar"],
            "name_en": r["name_en"],
            "next_title_id": id_of.get(r["next_title_code"]),
            "esco_occupation_uri": r["esco_occupation_uri"] or None,
        }
        for r in rows
    ]


def build() -> dict[str, int]:
    titles = _titles()
    title_id = {t["code"]: t["id"] for t in titles}
    dictionary = load_dictionary()
    extractor = KeywordExtractor(dictionary)
    skills = [
        {
            "id": i,
            "key": s["key"],
            "esco_id": s.get("esco_id"),
            "label_ar": s["label_ar"],
            "label_en": s["label_en"],
            "skill_type": s["skill_type"],
            "category": s["category"],
        }
        for i, s in enumerate(dictionary, start=1)
    ]
    skill_id = {s["key"]: s["id"] for s in skills}

    postings, posting_skills = [], []
    for pid, raw in enumerate(_read_csv(SOURCE_DIR / "job_postings.csv"), start=1):
        postings.append(
            {
                "id": pid,
                "posting_code": raw["posting_id"],
                "job_title_id": title_id[raw["job_title_code"]],
            }
        )
        text = " . ".join(
            x
            for x in (raw["title_as_posted"], raw["description_text"], raw["requirements_text"])
            if x
        )
        for found in extractor.extract(text):
            posting_skills.append(
                {
                    "posting_id": pid,
                    "skill_id": skill_id[found.skill_key],
                    "importance": found.importance,
                    "extraction_method": found.method,
                    "confidence": found.confidence,
                    "source_span": found.source_span,
                }
            )

    outputs = {
        "job_titles.json": titles,
        "skills.json": skills,
        "job_postings.json": postings,
        "posting_skills.json": posting_skills,
        "title_skill_profile.json": build_title_profiles(postings, posting_skills),
    }
    for name, rows in outputs.items():
        (DATA_DIR / name).write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    per_posting = Counter(ps["posting_id"] for ps in posting_skills)
    return {
        "postings": len(postings),
        "links": len(posting_skills),
        "postings_without_skills": sum(1 for p in postings if not per_posting[p["id"]]),
    }


if __name__ == "__main__":
    print(build())
