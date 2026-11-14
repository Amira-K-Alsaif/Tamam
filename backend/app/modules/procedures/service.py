"""Reads the extracted procedure catalog and searches it."""

import json
from pathlib import Path

from app.ai.arabic import normalize_arabic

from .schemas import Procedure

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = PROJECT_ROOT / "data/company/procedures.json"


class ProcedureNotFoundError(LookupError):
    pass


def load_catalog() -> list[Procedure]:
    """The extracted procedures. Empty until `python -m app.modules.procedures.cli` has run."""
    if not CATALOG_PATH.exists():
        return []
    return [Procedure.model_validate(item) for item in json.loads(CATALOG_PATH.read_text("utf-8"))]


def list_procedures(query: str | None = None, department: str | None = None) -> list[Procedure]:
    wanted = normalize_arabic(query or "")
    return [
        procedure
        for procedure in load_catalog()
        if (department is None or procedure.department == department)
        and wanted in normalize_arabic(_searchable_text(procedure))
    ]


def get_procedure(procedure_id: str) -> Procedure:
    for procedure in load_catalog():
        if procedure.id == procedure_id:
            return procedure
    raise ProcedureNotFoundError(procedure_id)


def _searchable_text(procedure: Procedure) -> str:
    return " ".join([procedure.title, procedure.summary, procedure.department, *procedure.forms])
