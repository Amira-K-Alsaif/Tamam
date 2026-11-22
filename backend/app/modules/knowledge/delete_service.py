"""Delete administrator-uploaded knowledge documents."""

import re

from supabase import Client

from app.modules.knowledge.storage_service import BUCKET_NAME


def delete_uploaded_document(db: Client, document_id: str) -> dict:
    """Delete an uploaded document and its stored original."""

    # Protect the initial company documents.
    if not re.fullmatch(r"upload-[0-9a-f]{32}", document_id):
        raise ValueError("Only uploaded documents can be deleted")

    result = db.table("documents").select("id,file_path").eq("id", document_id).limit(1).execute()

    if not result.data:
        raise LookupError("Document not found")

    file_path = result.data[0]["file_path"]
    prefix = f"uploads/{document_id}/"

    if not isinstance(file_path, str) or not file_path.startswith(prefix):
        raise ValueError("Invalid document storage path")

    filename = file_path[len(prefix) :]

    if not filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid document filename")

    # Remove the original file first.
    # If Storage fails, the database record remains.
    db.storage.from_(BUCKET_NAME).remove([file_path])

    # The database foreign key cascades deletion to chunks.
    deleted = db.table("documents").delete().eq("id", document_id).select("id").execute()

    if not deleted.data:
        raise RuntimeError("Storage file removed, but database deletion was not confirmed")

    return {
        "document_id": document_id,
        "status": "deleted",
    }
