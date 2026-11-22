import pytest

from app.modules.knowledge.upload_validation import (
    MAX_FILE_SIZE,
    validate_upload,
)


def test_accept_valid_document():
    assert validate_upload("policy.md", b"# Policy") == "policy.md"


@pytest.mark.parametrize(
    "filename",
    ["", "../secret.pdf", "policy.exe", "folder\\policy.pdf"],
)
def test_reject_invalid_filename(filename):
    with pytest.raises(ValueError):
        validate_upload(filename, b"content")


def test_reject_empty_document():
    with pytest.raises(ValueError):
        validate_upload("policy.md", b"")


def test_reject_oversized_document():
    with pytest.raises(ValueError):
        validate_upload("policy.md", b"a" * (MAX_FILE_SIZE + 1))
