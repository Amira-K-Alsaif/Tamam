# Tamam

An Arabic-first AI platform that helps new employees understand their company's
policies and procedures, and then plan their career growth.

- **Frontend:** React + Vite + TypeScript + Tailwind (`frontend/`)
- **Backend:** FastAPI + Python (`backend/`)
- **Data:** Supabase (PostgreSQL + pgvector)

Project rules live in [`CLAUDE.md`](CLAUDE.md). Module owners and shared data shapes live in
[`docs/team.md`](docs/team.md).

---

## Running locally

### Requirements

- Node.js `24.20.0` (see `.nvmrc`)
- Python `3.13` or newer

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Opens at http://localhost:5173

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment (Windows: `.venv\Scripts\activate`, macOS/Linux:
`source .venv/bin/activate`), then:

```bash
pip install -e ".[dev]"      # add ,rag to work on the AI features: ".[dev,rag]"
uvicorn app.main:app --reload --port 8000
```

Check it is running at http://localhost:8000/api/health. The API docs are at
http://localhost:8000/docs.

With both running, the frontend's side menu shows "الخادم متصل" (backend connected).

> On Windows, if creating the virtual environment fails because the path is too long,
> clone the project into a short path such as `C:\code\Tamam`.

### Checks to run before every pull request

```bash
cd frontend && npm run lint && npm test && npm run build
```

```bash
cd backend && ruff check . && ruff format --check . && pytest
```

---

## Project structure

Files marked 🔒 are configuration you rarely need to touch.

```
Tamam/
├── README.md              how to run and contribute (this file)
├── CLAUDE.md              project rules for coding agents and the team
├── docs/team.md           module owners and the shared data shapes
├── .github/
│   ├── workflows/ci.yml   checks that run on every pull request
│   └── pull_request_template.md
├── .gitignore             files git ignores, such as .env                🔒
├── .gitattributes         keeps line endings the same on every OS         🔒
├── .nvmrc                 Node.js version                                 🔒
│
├── frontend/              ── what the user sees
│   ├── index.html         the single HTML page React renders into
│   ├── package.json       dependencies and commands (npm run dev, npm test)
│   ├── vite.config.ts     dev server and build settings                   🔒
│   ├── tsconfig.json      TypeScript settings                             🔒
│   ├── .oxlintrc.json     lint rules                                      🔒
│   ├── .env.example       example environment variables (backend URL)
│   ├── CLAUDE.md          frontend rules
│   └── src/
│       ├── main.tsx       entry point: starts React and the router
│       ├── App.tsx        routes: which address opens which page
│       ├── index.css      design tokens: colors and fonts
│       ├── lib/
│       │   ├── api.ts     the only file that calls the backend
│       │   └── mockEmployee.ts   a fake signed-in employee until auth exists
│       ├── components/    shared pieces: side menu, Button, Card, StatusBadge, ...
│       ├── pages/HomePage.tsx
│       ├── modules/
│       │   ├── modules.ts the list of modules (menu, routes, home page cards)
│       │   └── <module>/  one folder per module, e.g. chat/ChatPage.tsx
│       └── test/setup.ts  test setup                                      🔒
│
└── backend/               ── logic, data, and AI
    ├── pyproject.toml     dependencies and tool settings
    ├── .python-version    Python version                                  🔒
    ├── .env.example       example environment variables (secrets go in .env)
    ├── CLAUDE.md          backend rules
    ├── app/
    │   ├── main.py        entry point: creates the app and registers every module
    │   ├── config.py      reads settings from environment variables
    │   └── modules/
    │       ├── __init__.py   the list of module routers the app registers
    │       └── <module>/     one folder per module, e.g. chat/router.py
    └── tests/             backend tests
```

The empty `__init__.py` files tell Python a folder is a package it can import from.
Leave them in place.

---

## How the app works

### Opening a page

```
npm run dev
   │
   ▼
index.html ──loads──▶ main.tsx ──renders──▶ App.tsx
                                              │ reads the address, e.g. /chat
                                              ▼
                                    AppShell (side menu)
                                       └── ChatPage (the page content)
```

1. `main.tsx` starts React inside `index.html`.
2. `App.tsx` matches the address: `/` opens the home page, `/chat` the chat module, and so on.
3. `AppShell` draws the side menu and places the matching page next to it.

### Calling the backend

```
AppShell ─▶ api.ts: getHealth() ─── GET /api/health ───▶ main.py
   ▲                                                       │
   └──── "backend connected" ◀────── {"status": "ok"} ◀────┘
```

Every call follows this path: a page calls a function in `api.ts`, which calls a route
on the backend, which returns JSON.

### A feature end to end

Each module follows the same shape. For example, asking a question in the chat module:

```
frontend/src/modules/chat/ChatPage.tsx     the user types a question
   │
   ▼
frontend/src/lib/api.ts                    askQuestion(question)
   │   POST /api/chat/ask
   ▼
backend/app/modules/chat/router.py         receives the request
   │
   ▼
backend/app/modules/chat/service.py        the logic: search documents, call the AI
   │
   ▼
returns { answer, sources }
   │
   ▼
ChatPage.tsx                               shows the answer and its sources
```

---

## Where your module lives

Every module has the same files. Replace `<module>` with yours (`chat`, `knowledge`,
`procedures`, `org-map`, `onboarding`, `career`).

| File | What goes in it |
|---|---|
| `frontend/src/modules/<module>/<Name>Page.tsx` | Your screen, built from its board on the design canvas |
| `frontend/src/modules/<module>/` | Any other components that only your screen uses |
| `frontend/src/lib/api.ts` | A function for each backend route you call (shared file: mention it in your PR) |
| `backend/app/modules/<module>/router.py` | Your API routes, under `/api/<module>/` |
| `backend/app/modules/<module>/service.py` | Your logic (create it when you need it) |
| `backend/app/modules/<module>/schemas.py` | The shapes of your requests and responses (create it when you need it) |
| `backend/tests/` | Tests for your module |

Working inside your own module folder keeps your work from conflicting with anyone else's.
Design reference for every screen: https://claude.ai/artifact/HgaMHyE9pcE3qRGCWjXqPB

---

## Workflow

1. Pull the latest `main` and create a branch named after your module: `feat/chat/citations`.
2. Work inside your module's folders.
3. Open a pull request against `main`.
4. Wait for **CI**, which runs lint, tests, and the build for both apps. It must be green.
5. Merge into `main`.

Never push directly to `main`.

## Protecting `main`

In **Settings → Rules → Rulesets**, add a rule on `main` that blocks direct pushes and
requires a pull request and passing CI checks (`Frontend` and `Backend`).

> Rulesets on private repositories need GitHub Pro, which students get free through the
> GitHub Student Developer Pack.
