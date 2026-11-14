# procedures: اختر الإجراء

Turns each company document of kind `procedure` into a structured procedure
(steps, requirements, forms, owner, duration) and serves it as a searchable catalog.

    data/company/documents/*.md ──cli──▶ data/company/procedures.json ──▶ GET /api/procedures

## Extraction (`extraction.py`)

1. The prompt (`prompts.py`) sends the document as data inside `<document>` and asks for JSON.
2. The reply is validated with `ExtractionResult` (`schemas.py`). Invalid output raises `ExtractionError`.
3. The evidence quote, forms, owner, and duration must appear in the document
   (compared after Arabic normalization). Anything the model invented is rejected.
4. The procedure id is the document id, so other modules use it as `procedure_id`.

Run it once the document set changes, then review and commit the result:

    cd backend && python -m app.modules.procedures.cli

It needs `TAMAM_GOOGLE_API_KEY` in `backend/.env` and prints a line for each document it rejected.

## API

| Route | Returns |
|---|---|
| `GET /api/procedures?q=&department=` | Procedures matching the search text and department |
| `GET /api/procedures/{id}` | One procedure with its source, or 404 |

Before the catalog file exists, the list is empty.
