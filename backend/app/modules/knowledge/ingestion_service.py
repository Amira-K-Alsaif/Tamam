"""Prepare uploaded documents for the knowledge database."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.ai.arabic import normalize_arabic
from app.modules.knowledge.schemas import Document
from app.modules.knowledge.service import build_chunks, extract_markdown
from app.modules.knowledge.upload_validation import validate_upload


def prepare_uploaded_document(
    filename: str,
    content: bytes,
    title: str,
    kind: str,
    department: str,
):
    filename = validate_upload(filename, content)

    if not title.strip() or not department.strip():
        raise ValueError("عنوان الوثيقة والقسم مطلوبان")

    document_id = f"upload-{uuid4().hex}"

    document = Document(
        id=document_id,
        title=title.strip(),
        kind=kind,
        department=department.strip(),
        file_path=f"uploads/{document_id}/{filename}",
        status="processing",
        updated_at=date.today(),
    )

    # Temporary files are removed after extraction.
    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / filename
        file_path.write_bytes(content)
        markdown = extract_markdown(file_path)

    if not markdown.strip():
        raise ValueError("لم يتم استخراج نص من الوثيقة")

    chunks = build_chunks(document, markdown)

    if not chunks:
        raise ValueError("لم يتم العثور على مقاطع قابلة للبحث")

    prepared_chunks = [
        {
            **chunk.model_dump(),
            "normalized_text": normalize_arabic(chunk.text),
        }
        for chunk in chunks
    ]

    return document, prepared_chunks
