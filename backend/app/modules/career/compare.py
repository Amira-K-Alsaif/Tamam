"""Compare the keyword dictionary with the model on the same job postings, for the report.

    cd backend && python -m app.modules.career.compare --limit 20   # try a few first
    cd backend && python -m app.modules.career.compare               # all postings

Model answers are cached in data/llm_skills_cache.json after every posting, so a re-run (or a
run that stopped half way) only pays for the postings that are not cached yet. A posting the
model fails on is retried once and then skipped, and the report lists it.
The report is written to data/career/extraction_comparison.md at the repository root.
"""

import argparse
import json
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from app.ai.llm import LLMNotConfiguredError, LLMUnavailableError

from .build_data import SOURCE_DIR, posting_text, read_postings
from .extraction import DATA_DIR, ExtractionError, KeywordExtractor, LLMExtractor, load_dictionary

CACHE_FILE = DATA_DIR / "llm_skills_cache.json"
REPORT_FILE = SOURCE_DIR / "extraction_comparison.md"


@dataclass
class Comparison:
    postings: int = 0
    failed: list[str] = field(default_factory=list)
    keyword_links: int = 0
    llm_links: int = 0
    both: int = 0
    keyword_empty: int = 0
    llm_empty: int = 0
    jaccard_sum: float = 0.0
    only_keyword: Counter = field(default_factory=Counter)
    only_llm: Counter = field(default_factory=Counter)

    def add(self, keyword: set[str], model: set[str]) -> None:
        self.postings += 1
        self.keyword_links += len(keyword)
        self.llm_links += len(model)
        self.both += len(keyword & model)
        self.keyword_empty += not keyword
        self.llm_empty += not model
        union = keyword | model
        self.jaccard_sum += len(keyword & model) / len(union) if union else 1.0
        self.only_keyword.update(keyword - model)
        self.only_llm.update(model - keyword)


RETRY_DELAY_SECONDS = 5


def _ask_model(model, text: str) -> list[str]:
    """The model's skill keys, retrying once when the provider times out or fails."""
    try:
        return sorted({s.skill_key for s in model.extract(text)})
    except LLMUnavailableError:
        time.sleep(RETRY_DELAY_SECONDS)
        return sorted({s.skill_key for s in model.extract(text)})


def compare(
    postings: list[dict], keyword, model, cache: dict[str, list[str]], on_new=lambda: None
) -> Comparison:
    """`on_new` runs after each newly cached answer, so the caller can save progress."""
    result = Comparison()
    for raw in postings:
        code, text = raw["posting_id"], posting_text(raw)
        if code not in cache:
            try:
                cache[code] = _ask_model(model, text)
            except (ExtractionError, LLMUnavailableError) as error:
                print(f"{code}: skipped ({type(error).__name__})")
                result.failed.append(code)
                continue
            on_new()
        result.add({s.skill_key for s in keyword.extract(text)}, set(cache[code]))
    return result


def _pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "-"


def render(c: Comparison, labels: dict[str, str]) -> str:
    n = c.postings
    if not n:
        return "# مقارنة استخراج المهارات\n\nما فيه إعلانات تمت مقارنتها.\n"
    rows = [
        ("الإعلانات المقارنة", n, n),
        ("مجموع المهارات المستخرجة", c.keyword_links, c.llm_links),
        ("متوسط المهارات لكل إعلان", f"{c.keyword_links / n:.1f}", f"{c.llm_links / n:.1f}"),
        ("إعلانات بدون أي مهارة", c.keyword_empty, c.llm_empty),
    ]
    lines = [
        "# مقارنة استخراج المهارات: القاموس مقابل النموذج",
        "",
        "| | القاموس | النموذج |",
        "|---|---|---|",
        *[f"| {name} | {k} | {m} |" for name, k, m in rows],
        "",
        f"- **الاتفاق (Jaccard):** {_pct(c.jaccard_sum, n)} في المتوسط لكل إعلان.",
        f"- **المهارات اللي لقوها الاثنين:** {c.both}.",
        f"- لو اعتبرنا النموذج هو المرجع: دقة القاموس (precision) {_pct(c.both, c.keyword_links)}،"
        f" وتغطيته (recall) {_pct(c.both, c.llm_links)}.",
    ]
    if c.failed:
        lines.append(
            f"- إعلانات رجع فيها النموذج رد غير صالح: {len(c.failed)} ({', '.join(c.failed)})."
        )
    for title, counter in (
        ("أكثر مهارات لقاها النموذج وفاتت القاموس", c.only_llm),
        ("أكثر مهارات لقاها القاموس والنموذج ما اعتبرها مطلوبة", c.only_keyword),
    ):
        lines += ["", f"## {title}", "", "| المهارة | عدد الإعلانات |", "|---|---|"]
        lines += [f"| {labels.get(k, k)} | {v} |" for k, v in counter.most_common(10)]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="compare only the first N postings")
    args = parser.parse_args()

    dictionary = load_dictionary()
    postings = read_postings()[: args.limit]
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}

    def save() -> None:
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    try:
        result = compare(
            postings, KeywordExtractor(dictionary), LLMExtractor(dictionary), cache, on_new=save
        )
    except LLMNotConfiguredError as error:
        raise SystemExit(str(error)) from error
    labels = {s["key"]: s["label_ar"] for s in dictionary}
    REPORT_FILE.write_text(render(result, labels), encoding="utf-8")
    print(
        f"{result.postings} postings compared, {len(result.failed)} skipped,"
        f" report: {Path(REPORT_FILE).resolve()}"
    )


if __name__ == "__main__":
    main()
