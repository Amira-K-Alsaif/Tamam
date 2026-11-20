"""Local document ingestion preparation for the knowledge factory."""

import json
import re
from pathlib import Path

from app.modules.knowledge.schemas import Chunk, Document

_HEADING = re.compile(r"^#{1,6}\s+(.+)$")
_SUPPORTED = {".md", ".txt", ".pdf", ".docx"}


def load_manifest(manifest_path: Path) -> list[Document]:
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("The manifest must be a list of documents")
    documents = [Document.model_validate(item) for item in records]
    ids = [doc.id for doc in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("Document IDs must be unique")
    return documents


def resolve_document_path(document: Document, company_dir: Path) -> Path:
    root = company_dir.resolve()
    path = (root / document.file_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Document path must remain within data/company")
    if path.suffix.lower() not in _SUPPORTED:
        raise ValueError(f"Unsupported document type: {path.suffix}")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def extract_markdown(path: Path) -> str:
    if path.suffix.lower() in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")

    # Import on demand: ordinary backend checks do not load a document conversion model.
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError("PDF/DOCX ingestion needs the approved Docling package") from exc

    conversion = DocumentConverter().convert(str(path))
    try:
        return conversion.document.export_to_markdown()
    finally:
        conversion.input.release()


def _sections(markdown: str, fallback_title: str) -> list[tuple[str, str]]:
    title = fallback_title
    lines: list[str] = []
    result: list[tuple[str, str]] = []
    for line in markdown.splitlines():
        match = _HEADING.match(line.strip())
        if match:
            if lines and "\n".join(lines).strip():
                result.append((title, "\n".join(lines).strip()))
            title = match.group(1).strip()
            lines = []
        else:
            lines.append(line)
    if "\n".join(lines).strip():
        result.append((title, "\n".join(lines).strip()))
    return result


def _windows(text: str, max_chars: int, overlap: int) -> list[str]:
    if max_chars <= 0 or not 0 <= overlap < max_chars:
        raise ValueError("max_chars must exceed overlap and be positive")
    windows = []
    position = 0
    while position < len(text):
        end = min(position + max_chars, len(text))
        if end < len(text):
            split = text.rfind(" ", position + max_chars // 2, end)
            if split > position:
                end = split + 1
        current = text[position:end].strip()
        if current:
            windows.append(current)
        if end == len(text):
            break
        position = max(position + 1, end - overlap)
    return windows


def build_chunks(document: Document, markdown: str, max_chars: int = 800) -> list[Chunk]:
    chunks: list[Chunk] = []
    for heading, section_text in _sections(markdown, document.title):
        for part in _windows(section_text, max_chars=max_chars, overlap=min(100, max_chars // 4)):
            chunks.append(
                Chunk(
                    id=f"{document.id}-c{len(chunks) + 1:03d}",
                    document_id=document.id,
                    section_title=heading,
                    text=part,
                )
            )
    return chunks
