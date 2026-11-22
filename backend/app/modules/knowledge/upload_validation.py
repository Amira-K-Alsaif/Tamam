"""Validate files before knowledge ingestion."""

from pathlib import Path

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


def validate_upload(filename: str, content: bytes) -> str:
    """Validate an uploaded document and return its filename."""

    if not filename or not filename.strip():
        raise ValueError("اسم الملف مطلوب")

    filename = filename.strip()

    if filename != Path(filename).name or "\\" in filename or "\x00" in filename:
        raise ValueError("اسم الملف غير صالح")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("نوع الملف غير مدعوم")

    if not content:
        raise ValueError("الملف فارغ")

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("حجم الملف يتجاوز 20 MB")

    return filename
