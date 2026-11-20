"""Save knowledge documents and embeddings to Supabase."""

from supabase import Client

from app.modules.knowledge.schemas import Document

EMBEDDING_DIMENSIONS = 1024
BATCH_SIZE = 10


def save_document_to_database(
    db: Client,
    document: Document,
    chunks: list[dict],
) -> None:
    """Save a new document with its embedded chunks."""

    if document.status != "processing":
        raise ValueError("Document must be processing")

    if not chunks:
        raise ValueError("No chunks to save")

    rows = []

    for chunk in chunks:
        if chunk["document_id"] != document.id:
            raise ValueError("Chunk belongs to another document")

        embedding = chunk.get("embedding")

        if embedding is None or len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError("Invalid embedding dimensions")

        rows.append(
            {
                "id": chunk["id"],
                "document_id": document.id,
                "section_title": chunk["section_title"],
                "page": chunk.get("page"),
                "text": chunk["text"],
                "normalized_text": chunk.get("normalized_text"),
                "embedding": embedding,
            }
        )

    document_created = False

    try:
        # Create document with processing status.
        db.table("documents").insert(document.model_dump(mode="json")).execute()

        document_created = True

        # Insert chunks in manageable batches.
        for start in range(0, len(rows), BATCH_SIZE):
            batch = rows[start : start + BATCH_SIZE]

            db.table("chunks").insert(batch).execute()

        # Mark as ready only after all chunks are saved.
        db.table("documents").update({"status": "ready"}).eq("id", document.id).execute()

    except Exception:
        if document_created:
            # Deleting the document cascades to its chunks.
            db.table("documents").delete().eq("id", document.id).execute()

        raise
