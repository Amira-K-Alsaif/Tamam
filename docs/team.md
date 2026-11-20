# Team, modules, and shared contracts

Full plan (roles, weekly schedule, competitors):
https://claude.ai/artifact/Pyo1HYmJhwXu1tAfVBk5Ln

## Owners

| # | Module | Arabic name | Owner | Shared duty |
|---|---|---|---|---|
| 1 | `chat` | اسأل عن إجراء | Amira (`Amira-K-Alsaif`) | Tech lead: repository and merges |
| 2 | `knowledge` | مصنع المعرفة | Gamar (`gamaraljaliy`) | Evaluation question set (`data/eval/`) |
| 3 | `procedures` | اختر الإجراء | Shoog (`shoog4321`) | Design tokens and app shell |
| 4 | `org-map` | خريطة الشركة | Sara (`saraalmazroa`) | Deployment (Vercel, Railway) |
| 5 | `onboarding` | مساري التأهيلي | Gala (`ghalaIter`) | Auth and the shared employee profile |
| 6 | `career` | مساري المهني | Batool (`batool2044`) | Competitor research and the final presentation |

## What modules 4 and 5 do

Screens for every module: https://claude.ai/artifact/HgaMHyE9pcE3qRGCWjXqPB

**4 · `org-map` (خريطة الشركة)** — the company's structure: the CEO, each department
with its head and teams, and the people in each team. Each person shows their title,
their relation to the viewer (manager, mentor), contact details, what to contact them
about, and the procedures they approve. Search answers "who do I talk to about X?".

**5 · `onboarding` (مساري التأهيلي)** — a roadmap of everything a new employee is
missing, built from a starting assessment:

- **Knowledge gaps**: diagnostic questions score each topic; low topics become lessons
  with a short quiz, and the roadmap says why each one was added.
- **Missing access**: the systems and permissions the employee's job title needs, each
  with its status (active, requested, missing), why it is needed, and the steps to get
  it (form, approver, expected time).
- **People to meet**: key contacts from the company map (mentor, approvers).

The roadmap is grouped by week and reorders as quizzes are retaken and access is granted.

## Milestones

| Date | Milestone |
|---|---|
| Tue 28 Oct | Shared contracts below agreed; every module runs on mock data |
| Tue 4 Nov | Every module's basic level works on its own |
| Tue 11 Nov | Integrated version deployed |
| Sun 16 Nov | Feature freeze: fixes and polish only |
| Wed 19 Nov | Delivery and demo |

## Shared contracts

Agree on these in the first team meeting and write them here. Until then, each module
uses mock data in exactly this shape. A change here needs approval from every module
that uses the contract.

### Employee profile (owner: 5, used by 3, 4, 5, 6)

    id, full_name, department_id, team, job_title, manager_id, years_of_experience,
    role (employee | admin)

### Department (owner: 4, used by 4, 5)

    id, name, head_id, parent_id, teams[]

### Contact responsibility (owner: 4, used by 3, 4, 5)

    employee_id, topic, procedure_id (optional)

### Access item (owner: 5, used by 3, 5)

    id, system_name, required_for_job_titles[], procedure_id, approver_role, expected_days
    per employee: status (active | requested | missing)

### Assessment result (owner: 5, used by 5, 6)

    employee_id, topic, score (0-100), taken_at

### Document (owner: 2, used by 1, 3)

    id, title, kind (policy | procedure | form | faq), department, file_path, status, updated_at

### Chunk (owner: 2, used by 1, 3, 5)

    id, document_id, section_title, page, text, embedding (vector)

### Source citation in any AI answer (owner: 1, used by everyone who shows sources)

    document_id, document_title, page, section_title, quote

`page` is null for documents without pages, such as Markdown.
