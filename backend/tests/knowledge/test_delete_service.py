"""Tests for deleting uploaded knowledge documents."""

from unittest.mock import MagicMock

import pytest

from app.modules.knowledge.delete_service import delete_uploaded_document

DOCUMENT_ID = "upload-" + "a" * 32
FILE_PATH = f"uploads/{DOCUMENT_ID}/policy.md"


def mock_database():
    db = MagicMock()
    table = db.table.return_value

    table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [
        {"id": DOCUMENT_ID, "file_path": FILE_PATH}
    ]

    table.delete.return_value.eq.return_value.select.return_value.execute.return_value.data = [
        {"id": DOCUMENT_ID}
    ]

    return db


def test_delete_uploaded_document():
    db = mock_database()

    result = delete_uploaded_document(db, DOCUMENT_ID)

    assert result["status"] == "deleted"
    assert result["document_id"] == DOCUMENT_ID

    db.storage.from_.assert_called_once_with("knowledge-documents")
    db.storage.from_.return_value.remove.assert_called_once_with([FILE_PATH])
    db.table.return_value.delete.assert_called_once()


def test_protect_original_documents():
    db = mock_database()

    with pytest.raises(ValueError):
        delete_uploaded_document(db, "annual-leave")

    db.table.assert_not_called()


def test_document_not_found():
    db = mock_database()
    table = db.table.return_value

    table.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = []

    with pytest.raises(LookupError):
        delete_uploaded_document(db, DOCUMENT_ID)

    db.storage.from_.assert_not_called()


def test_storage_failure_keeps_database_record():
    db = mock_database()
    db.storage.from_.return_value.remove.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(RuntimeError, match="Storage unavailable"):
        delete_uploaded_document(db, DOCUMENT_ID)

    db.table.return_value.delete.assert_not_called()


def test_database_deletion_not_confirmed():
    db = mock_database()
    table = db.table.return_value

    table.delete.return_value.eq.return_value.select.return_value.execute.return_value.data = []

    with pytest.raises(RuntimeError, match="not confirmed"):
        delete_uploaded_document(db, DOCUMENT_ID)
