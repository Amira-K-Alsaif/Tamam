"""Tests for the knowledge upload pipeline."""

from datetime import date
from unittest.mock import MagicMock, Mock

import pytest

from app.modules.knowledge import upload_pipeline
from app.modules.knowledge.schemas import Document


@pytest.fixture
def prepared_upload(monkeypatch):
    document_id = "upload-" + "a" * 32

    document = Document(
        id=document_id,
        title="سياسة تجريبية",
        kind="policy",
        department="الموارد البشرية",
        file_path=f"uploads/{document_id}/test.md",
        status="processing",
        updated_at=date.today(),
    )

    chunks = [
        {
            "id": f"{document_id}-c001",
            "document_id": document_id,
            "section_title": "الغرض",
            "text": "هذه وثيقة تجريبية.",
        }
    ]

    embedded_chunks = [{**chunks[0], "embedding": [0.0] * 1024}]

    monkeypatch.setattr(
        upload_pipeline,
        "prepare_uploaded_document",
        lambda **kwargs: (document, chunks),
    )

    monkeypatch.setattr(
        upload_pipeline,
        "embed_chunks",
        lambda items: embedded_chunks,
    )

    monkeypatch.setattr(
        upload_pipeline,
        "upload_original_document",
        lambda db, doc, content: document.file_path,
    )

    return document, embedded_chunks


def run_upload(db):
    return upload_pipeline.process_document_upload(
        db=db,
        filename="test.md",
        content=b"# Test",
        title="سياسة تجريبية",
        kind="policy",
        department="الموارد البشرية",
    )


def test_successful_upload(monkeypatch, prepared_upload):
    document, chunks = prepared_upload
    db = MagicMock()

    save = Mock()
    monkeypatch.setattr(upload_pipeline, "save_document_to_database", save)

    result = run_upload(db)

    assert result["status"] == "ready"
    assert result["document_id"] == document.id
    assert result["chunks_count"] == 1

    save.assert_called_once_with(db, document, chunks)
    db.storage.from_.assert_not_called()


def test_storage_cleanup_when_database_fails(monkeypatch, prepared_upload):
    document, _ = prepared_upload
    db = MagicMock()

    def fail_save(*args):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(
        upload_pipeline,
        "save_document_to_database",
        fail_save,
    )

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        run_upload(db)

    db.storage.from_.assert_called_once_with("knowledge-documents")
    db.storage.from_.return_value.remove.assert_called_once_with([document.file_path])
