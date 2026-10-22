# Backend Agent Instructions

Read the root `CLAUDE.md` first. This file adds the backend, data, and AI rules.

## Structure

    app/
      main.py                 app factory, CORS, health, router registration
      config.py               settings from environment variables (prefix TAMAM_)
      ai/                     LLM and embedding calls; nothing else calls them
      modules/<module>/
        router.py             HTTP routes only
        service.py            business logic
        schemas.py            Pydantic request/response models (the API contract)
        repository.py         database access
        prompts/              prompt files for this module
    tests/
      <module>/               tests for each module

Create `service.py`, `schemas.py`, `repository.py`, and `prompts/` in a module when it
first needs them.

## Layering

    router → service → repository → database
                 ↘ app/ai

- Routes parse input, call one service function, and return a schema. No business logic.
- Services hold the rules and know nothing about HTTP.
- Repositories hold all database access.
- Never return database rows directly from a route; map them to a response schema.

## API

- Every route lives under `/api/<module>/...` (each module router already sets the prefix).
- Request and response bodies are Pydantic models in `schemas.py`.
- Validate input at the boundary. Return meaningful status codes (400, 401, 403, 404, 422).
- Error responses never include stack traces, SQL, prompts, or provider error details.

## Authentication and authorization

- Supabase Auth issues the user's JWT. The backend verifies it on every protected route.
- The current user comes from the verified token, never from a user id sent by the client.
- Every query on employee-owned data (profile, quiz results, career plan, uploaded CV)
  is scoped to the current user. Admin routes (document upload) check the admin role.

## AI boundary (`app/ai/`)

- Exposes Tamam-level functions such as `embed(texts)`, `generate(...)`, and
  `generate_structured(..., schema)`. Modules call these, never a provider SDK.
- Model names, API keys, timeouts, and retries are configured here, from settings.
- Every external call has a timeout. Retry only transient failures, a few times at most.
- Log the model, latency, and token usage of each call. Never log API keys or CV contents.

## RAG rules

- Chunks keep their source: document id, title, page or section, and the chunk text.
- Retrieval returns the source with every chunk, and the answer cites it.
- If the best chunks are not relevant enough, answer that the information was not found.
- Normalize Arabic identically at ingestion and at query time
  (alef forms, taa marbuta and haa, alef maqsura and yaa, tatweel, diacritics).
- Retrieved text is wrapped as data in the prompt and never treated as instructions.

## Long-running work

Document ingestion and plan generation can take time.
Represent their state explicitly (`pending`, `processing`, `done`, `failed`), never hold a
database transaction open while waiting on an AI call, and make failures visible.

## Database

- PostgreSQL on Supabase with `pgvector`.
- Schema changes are migration files committed with the code. Never edit an applied migration.
- Develop migrations against a local or throwaway database, not the shared one.

## Configuration and secrets

- Configuration comes from environment variables prefixed `TAMAM_`, read in `app/config.py`.
  Document every new variable in `.env.example` with a safe example value.
- Secrets never appear in code, tests, logs, or error messages.

## Tests

- pytest with FastAPI's `TestClient`.
- Fake `app/ai/` in tests. Normal tests never call a real LLM, embedding model, or Supabase.
- Test the rules that matter: citations present, "not found" when nothing matches,
  one user cannot read another user's data, invalid model output is rejected.

Commands (from `backend/`, inside a virtual environment):

    pip install -e ".[dev]"
    uvicorn app.main:app --reload --port 8000
    ruff check . && ruff format --check . && pytest
