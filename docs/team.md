# Team, modules, and shared contracts

Full plan (roles, weekly schedule, competitors):
https://claude.ai/artifact/Pyo1HYmJhwXu1tAfVBk5Ln

## Owners

Replace each "Member N" with a name and GitHub username.

| # | Module | Arabic name | Owner | Shared duty |
|---|---|---|---|---|
| 1 | `chat` | اسأل عن إجراء | Member 1 | Tech lead: repository and merges |
| 2 | `knowledge` | مصنع المعرفة | Member 2 | Evaluation question set (`data/eval/`) |
| 3 | `procedures` | اختر الإجراء | Member 3 | Design tokens and app shell |
| 4 | `procedure-map` | خريطة الإجراءات | Member 4 | Deployment (Vercel, Railway) |
| 5 | `onboarding` | مساري التأهيلي | Member 5 | Auth and the shared employee profile |
| 6 | `career` | مساري المهني | Member 6 | Competitor research and the final presentation |

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

### Employee profile (owner: 5, used by 3, 5, 6)

    id, full_name, department, job_title, years_of_experience, role (employee | admin)

### Document (owner: 2, used by 1, 3, 4)

    id, title, kind (policy | procedure | form | faq), department, file_path, status, updated_at

### Chunk (owner: 2, used by 1, 3, 4, 5)

    id, document_id, section_title, page, text, embedding (vector)

### Source citation in any AI answer (owner: 1, used by everyone who shows sources)

    document_id, document_title, page, section_title, quote
