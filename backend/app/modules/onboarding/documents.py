"""The company documents behind the assessment and the lessons, from data/company/manifest.json."""

import json
from functools import lru_cache
from pathlib import Path

COMPANY_DIR = Path(__file__).resolve().parents[4] / "data" / "company"
# Questions written once from each policy by build_questions.py, with their answers.
QUESTION_BANK = Path(__file__).resolve().parent / "data" / "policy_questions.json"

# Policies every employee should know, after the ones of their own department.
COMPANY_WIDE = ["infosec", "code-conduct", "data-privacy", "attendance", "annual-leave"]


@lru_cache
def _manifest() -> list[dict]:
    return json.loads((COMPANY_DIR / "manifest.json").read_text(encoding="utf-8"))


def _titles() -> dict[str, str]:
    return {document["id"]: document["title"] for document in _manifest()}


def policies() -> list[tuple[str, str]]:
    """(id, title) of every company policy, the documents the assessment can ask about."""
    return [(d["id"], d["title"]) for d in _manifest() if d["kind"] == "policy"]


def policies_for(team: str, count: int) -> list[str]:
    """The policies of the employee's own department first, then the company-wide ones."""
    own = [d["id"] for d in _manifest() if d["kind"] == "policy" and d["department"] == team]
    return list(dict.fromkeys(own[:2] + COMPANY_WIDE))[:count]


@lru_cache
def bank() -> dict[str, list[dict]]:
    """The saved questions per policy, or none if the bank has not been built."""
    if not QUESTION_BANK.is_file():
        return {}
    return json.loads(QUESTION_BANK.read_text(encoding="utf-8"))


def topic_for(document_id: str) -> str:
    """A lesson's topic is its policy's title, the same name the assessment scored."""
    title = _titles().get(document_id)
    if title is None:
        raise LookupError(f"No lesson for document: {document_id}")
    return title


def document_for(topic: str) -> str | None:
    """The policy a scored topic came from."""
    return next((doc_id for doc_id, title in _titles().items() if title == topic), None)


def load_document(document_id: str) -> tuple[str, str]:
    """The document's title and Markdown text."""
    title = _titles().get(document_id)
    if title is None:
        raise LookupError(f"Unknown document: {document_id}")
    markdown = (COMPANY_DIR / "documents" / f"{document_id}.md").read_text(encoding="utf-8")
    return title, markdown
