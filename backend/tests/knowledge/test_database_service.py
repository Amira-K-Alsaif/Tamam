"""Tests for knowledge database operations."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.modules.knowledge.database_service import save_document_to_database
from app.modules.knowledge.schemas import Document


def sample_document():
    return Document(
        id="upload-" + "a" * 32,
        title="سياسة تجريبية",
        kind="policy",
        department="الموارد البشرية",
        file_path="uploads/test-policy.md",
        status="processing",
        updated_at=date.today(),
    )


def sample_chunk(document):
    return {
        "id": f"{document.id}-c001",
        "document_id": document.id,
        "section_title": "الغرض",
        "text": "هذه سياسة تجريبية.",
        "normalized_text": "هذه سياسه تجريبيه.",
        "page": None,
        "embedding": [0.0] * 1024,
    }


def mock_database():
    db = MagicMock()
    documents = MagicMock()
    chunks = MagicMock()

    db.table.side_effect = lambda name: {
        "documents": documents,
        "chunks": chunks,
    }[name]

    return db, documents, chunks


def test_save_document_successfully():
    db, documents, chunks = mock_database()
    document = sample_document()

    save_document_to_database(db, document, [sample_chunk(document)])

    documents.insert.assert_called_once()
    chunks.insert.assert_called_once()
    documents.update.assert_called_once_with({"status": "ready"})
    documents.delete.assert_not_called()


def test_cleanup_if_chunks_fail():
    db, documents, chunks = mock_database()
    document = sample_document()

    chunks.insert.side_effect = RuntimeError("Simulated database failure")

    with pytest.raises(RuntimeError):
        save_document_to_database(db, document, [sample_chunk(document)])

    documents.delete.assert_called_once()
    documents.delete.return_value.eq.assert_called_once_with("id", document.id)


def test_reject_invalid_embedding():
    db, _, _ = mock_database()
    document = sample_document()
    chunk = sample_chunk(document)
    chunk["embedding"] = [0.1, 0.2]

    with pytest.raises(ValueError):
        save_document_to_database(db, document, [chunk])

    db.table.assert_not_called()
