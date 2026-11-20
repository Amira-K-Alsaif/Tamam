"""Admin-only policy conflict candidates, update history, and data quality audit."""

import logging
import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.modules.knowledge.admin_auth import require_admin
from app.modules.knowledge.policy_review import audit_knowledge_data, find_policy_conflicts

logger = logging.getLogger(__name__)
router = APIRouter()


def _database():
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    url = os.getenv("SUPABASE_URL")
    secret = os.getenv("SUPABASE_SECRET_KEY")
    if not url or not secret:
        raise HTTPException(status_code=503, detail="خدمة الوثائق غير مهيأة")
    return create_client(url, secret)


def _rows(db, table: str, columns: str, cap: int = 10000):
    """Page database rows: the PostgREST response limit is not assumed unlimited."""
    rows = []
    page_size = 500
    for offset in range(0, cap, page_size):
        result = (
            db.table(table)
            .select(columns)
            .order("id")
            .range(offset, min(offset + page_size - 1, cap - 1))
            .execute()
        )
        batch = result.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            return rows
    # No partial results: incomplete comparisons can produce misleading audits.
    raise RuntimeError(f"{table} exceeds the review limit ({cap} rows)")


def _snapshot(db):
    docs = _rows(db, "documents", "id,title,kind,department,status,updated_at")
    chunks = _rows(db, "chunks", "id,document_id,section_title,text")
    return docs, chunks


@router.get("/conflicts")
def get_policy_conflicts(admin_id: Annotated[str, Depends(require_admin)]):
    """Flag potential numeric policy mismatches with quotes and source IDs."""
    try:
        docs, chunks = _snapshot(_database())
        candidates = find_policy_conflicts(docs, chunks)
        return {
            "candidates": candidates,
            "count": len(candidates),
            "disclaimer": "مؤشرات أولية للمراجعة البشرية وليست تعارضات مؤكدة",
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to review policy conflicts")
        raise HTTPException(status_code=500, detail="تعذر فحص تعارض السياسات") from None


@router.get("/quality")
def get_knowledge_quality(admin_id: Annotated[str, Depends(require_admin)]):
    """Audit duplicate, missing and orphaned data; read-only by design."""
    try:
        docs, chunks = _snapshot(_database())
        return audit_knowledge_data(docs, chunks)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to audit knowledge data")
        raise HTTPException(status_code=500, detail="تعذر تدقيق جودة البيانات") from None


@router.get("/alerts")
def get_policy_alerts(admin_id: Annotated[str, Depends(require_admin)]):
    """Retrieve persisted policy create/update/delete events (requires SQL migration)."""
    try:
        db = _database()
        result = (
            db.table("knowledge_change_events")
            .select("id,document_id,document_title,event_type,changed_at")
            .order("changed_at", desc=True)
            .limit(50)
            .execute()
        )
        return {"alerts": result.data or []}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to read policy update events")
        raise HTTPException(status_code=500, detail="تعذر عرض تنبيهات السياسات") from None
