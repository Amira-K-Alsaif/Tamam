"""Pipeline step 1: the company's document chunks, prepared by the knowledge module.

The knowledge module reads data/company/, splits each document by heading, and writes
data/processed/chunks.jsonl. The chat only reads that file, so the two modules share
the Chunk contract in docs/team.md, not code.

Prepare the file from backend/ with:  python -m app.modules.knowledge.cli
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CHUNKS_FILE = PROJECT_ROOT / "data/processed/chunks.jsonl"
MANIFEST_FILE = PROJECT_ROOT / "data/company/manifest.json"


class CorpusNotPreparedError(RuntimeError):
    """Raised when the knowledge module has not written the chunk file yet."""


@dataclass(frozen=True)
class Chunk:
    """A searchable piece of a company document, with everything needed to cite it."""

    id: str
    document_id: str
    document_title: str
    section_title: str
    page: int | None  # None for documents without pages, such as Markdown
    text: str

    @property
    def search_text(self) -> str:
        """The text that search reads: the chunk plus its document and section titles.

        A chunk such as «المدة المتوقعة ثلاثة أيام عمل» does not say what it is about.
        Prefixing the titles gives search that context.
        """
        return f"{self.document_title} · {self.section_title}\n{self.text}"


def load_chunks(
    chunks_file: Path = CHUNKS_FILE, manifest_file: Path = MANIFEST_FILE
) -> list[Chunk]:
    """Reads the knowledge module's chunks and adds each document's title from the manifest."""
    if not chunks_file.is_file():
        raise CorpusNotPreparedError(
            f"{chunks_file} is missing. Run: python -m app.modules.knowledge.cli"
        )

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    titles = {document["id"]: document["title"] for document in manifest}

    chunks = []
    for line in chunks_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        chunks.append(
            Chunk(
                id=row["id"],
                document_id=row["document_id"],
                document_title=titles[row["document_id"]],
                section_title=row["section_title"],
                page=row.get("page"),
                text=row["text"],
            )
        )
    return chunks


@lru_cache
def all_chunks() -> tuple[Chunk, ...]:
    """Every company chunk, read once per process."""
    return tuple(load_chunks())
