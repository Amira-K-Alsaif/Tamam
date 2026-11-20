"""Knowledge factory API endpoints."""

import logging
import os
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.modules.knowledge.admin_auth import require_admin
from app.modules.knowledge.review_router import router as review_router
from app.modules.knowledge.upload_validation import (
    MAX_FILE_SIZE,
    validate_upload,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)


@router.post("/documents", status_code=201)
def upload_document(
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    kind: Annotated[
        Literal["policy", "procedure", "form", "faq"],
        Form(),
    ],
    department: Annotated[str, Form()],
    admin_id: Annotated[str, Depends(require_admin)],
):
    """Allow an authenticated administrator to upload a document."""

    # Read at most 20 MB + 1 byte to detect oversized files.
    content = file.file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="حجم الملف يتجاوز 20 MB",
        )

    try:
        filename = validate_upload(file.filename or "", content)

        # Heavy dependencies are imported only when needed.
        from dotenv import load_dotenv
        from supabase import create_client

        from app.modules.knowledge.upload_pipeline import (
            process_document_upload,
        )

        load_dotenv(Path(__file__).resolve().parents[3] / ".env")

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SECRET_KEY")

        if not url or not key:
            raise HTTPException(
                status_code=503,
                detail="خدمة الوثائق غير مهيأة",
            )

        db = create_client(url, key)

        result = process_document_upload(
            db=db,
            filename=filename,
            content=content,
            title=title,
            kind=kind,
            department=department,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception:
        logger.exception("Knowledge document upload failed")
        raise HTTPException(
            status_code=500,
            detail="تعذر معالجة الوثيقة",
        ) from None


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    admin_id: Annotated[str, Depends(require_admin)],
):
    """Delete an uploaded knowledge document (admin only)."""

    try:
        from dotenv import load_dotenv
        from supabase import create_client

        from app.modules.knowledge.delete_service import (
            delete_uploaded_document,
        )

        load_dotenv(Path(__file__).resolve().parents[3] / ".env")

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SECRET_KEY")

        if not url or not key:
            raise HTTPException(
                status_code=503,
                detail="خدمة الوثائق غير مهيأة",
            )

        db = create_client(url, key)

        return delete_uploaded_document(db, document_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception:
        logger.exception("Knowledge document deletion failed")
        raise HTTPException(
            status_code=500,
            detail="تعذر حذف الوثيقة",
        ) from None


@router.get("/documents")
def list_documents(
    admin_id: Annotated[str, Depends(require_admin)],
):
    """List knowledge documents for authenticated admins."""

    try:
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv(Path(__file__).resolve().parents[3] / ".env")

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SECRET_KEY")

        if not url or not key:
            raise HTTPException(
                status_code=503,
                detail="خدمة الوثائق غير مهيأة",
            )

        db = create_client(url, key)

        response = (
            db.table("documents")
            .select("id,title,kind,department,status,updated_at")
            .order("title")
            .execute()
        )

        return {"documents": response.data}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to list knowledge documents")
        raise HTTPException(
            status_code=500,
            detail="تعذر عرض الوثائق",
        ) from None


router.include_router(review_router)
