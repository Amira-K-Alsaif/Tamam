"""Coordinate knowledge document upload and processing."""

from supabase import Client

from app.modules.knowledge.database_service import (
    save_document_to_database,
)
from app.modules.knowledge.embedding_service import embed_chunks
from app.modules.knowledge.ingestion_service import prepare_uploaded_document
from app.modules.knowledge.storage_service import (
    BUCKET_NAME,
    upload_original_document,
)


def process_document_upload(
    db: Client,
    filename: str,
    content: bytes,
    title: str,
    kind: str,
    department: str,
) -> dict:
    """Process and save a new knowledge document."""

    # 1. Validate, extract text, and build chunks.
    document, chunks = prepare_uploaded_document(
        filename=filename,
        content=content,
        title=title,
        kind=kind,
        department=department,
    )

    # 2. Generate embeddings before modifying storage.
    embedded_chunks = embed_chunks(chunks)

    uploaded_path = None

    try:
        # 3. Save the original file in private Storage.
        uploaded_path = upload_original_document(db, document, content)

        # 4. Save document metadata and searchable chunks.
        save_document_to_database(db, document, embedded_chunks)

    except Exception as exc:
        # Compensating cleanup if database saving fails.
        if uploaded_path is not None:
            try:
                db.storage.from_(BUCKET_NAME).remove([uploaded_path])
            except Exception as cleanup_error:
                exc.add_note(f"Storage cleanup failed: {cleanup_error}")
        raise

    return {
        "document_id": document.id,
        "title": document.title,
        "status": "ready",
        "chunks_count": len(embedded_chunks),
        "file_path": uploaded_path,
    }
