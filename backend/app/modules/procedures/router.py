"""Procedure catalog. Owned by one team member; see docs/team.md."""

from fastapi import APIRouter, HTTPException

from . import forms, service
from .schemas import CompanyForm, Procedure

router = APIRouter(prefix="/api/procedures", tags=["procedures"])


@router.get("", response_model=list[Procedure])
def list_procedures(q: str | None = None, department: str | None = None) -> list[Procedure]:
    """The catalog, optionally filtered by a search text and a department."""
    return service.list_procedures(q, department)


# Declared before /{procedure_id} so "forms" is not read as a procedure id.
@router.get("/forms", response_model=list[CompanyForm])
def list_forms() -> list[CompanyForm]:
    """Company forms with their fields, and which fields the employee profile fills."""
    return forms.list_forms()


@router.get("/forms/{form_id}", response_model=CompanyForm)
def get_form(form_id: str) -> CompanyForm:
    try:
        return forms.get_form(form_id)
    except forms.FormNotFoundError:
        raise HTTPException(status_code=404, detail="ما لقيت هذا النموذج.") from None


@router.get("/{procedure_id}", response_model=Procedure)
def get_procedure(procedure_id: str) -> Procedure:
    try:
        return service.get_procedure(procedure_id)
    except service.ProcedureNotFoundError:
        raise HTTPException(status_code=404, detail="ما لقيت هذا الإجراء.") from None
