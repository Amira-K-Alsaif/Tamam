"""Procedure catalog. Owned by one team member; see docs/team.md."""

from fastapi import APIRouter, HTTPException

from . import service
from .schemas import Procedure

router = APIRouter(prefix="/api/procedures", tags=["procedures"])


@router.get("", response_model=list[Procedure])
def list_procedures(q: str | None = None, department: str | None = None) -> list[Procedure]:
    """The catalog, optionally filtered by a search text and a department."""
    return service.list_procedures(q, department)


@router.get("/{procedure_id}", response_model=Procedure)
def get_procedure(procedure_id: str) -> Procedure:
    try:
        return service.get_procedure(procedure_id)
    except service.ProcedureNotFoundError:
        raise HTTPException(status_code=404, detail="ما لقيت هذا الإجراء.") from None
