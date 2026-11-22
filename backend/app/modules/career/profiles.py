"""Skill profile per job title: the share of its postings that ask for each skill."""

from collections import defaultdict


def build_title_profiles(postings: list[dict], posting_skills: list[dict]) -> list[dict]:
    total: dict[int, int] = defaultdict(int)
    title_of: dict[int, int] = {}
    for p in postings:
        total[p["job_title_id"]] += 1
        title_of[p["id"]] = p["job_title_id"]

    counts: dict[tuple[int, int], list[int]] = defaultdict(lambda: [0, 0])
    for ps in posting_skills:
        k = (title_of[ps["posting_id"]], ps["skill_id"])
        counts[k][0] += 1
        counts[k][1] += ps["importance"] == "required"

    rows = [
        {
            "job_title_id": title_id,
            "skill_id": skill_id,
            "postings_count": n,
            "frequency": round(n / total[title_id], 2),
            "required_ratio": round(required / n, 2),
        }
        for (title_id, skill_id), (n, required) in counts.items()
    ]
    rows.sort(key=lambda r: (r["job_title_id"], -r["frequency"]))
    return rows
