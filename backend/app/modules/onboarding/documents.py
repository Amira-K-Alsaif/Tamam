"""The company documents behind the assessment and the lessons, from data/company/manifest.json."""

import json
from functools import lru_cache
from pathlib import Path

COMPANY_DIR = Path(__file__).resolve().parents[4] / "data" / "company"


@lru_cache
def _manifest() -> list[dict]:
    return json.loads((COMPANY_DIR / "manifest.json").read_text(encoding="utf-8"))


def _titles() -> dict[str, str]:
    return {document["id"]: document["title"] for document in _manifest()}


def policies() -> list[tuple[str, str]]:
    """(id, title) of every company policy, the documents the assessment can ask about."""
    return [(d["id"], d["title"]) for d in _manifest() if d["kind"] == "policy"]


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
