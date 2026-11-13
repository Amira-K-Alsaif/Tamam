# Chat module — «اسأل عن إجراء»

Owner: Amira (`Amira-K-Alsaif`)

An employee asks a question in Arabic, including Saudi dialect. Tamam answers **only
from the company's documents**, shows **where each fact came from**, and says
**«ما لقيت»** when the documents don't contain the answer, instead of guessing.

This is Retrieval-Augmented Generation (RAG): find the right passages first, then let a
language model write the answer from those passages alone.

---

## How a question is answered

```
"أبي أشتغل من البيت"
        │
 1. Chunking ─────────── documents were split once into small chunks that know their source
        │
 2. Hybrid search ────── meaning search (embeddings) + keyword search (BM25), merged by rank
        │                → up to 10 candidates
 3. Reranking ────────── a cross-encoder reads each candidate with the question
        │                → best 3
 4. Prompt ───────────── instructions + numbered sources + question
        │
 5. Generation ───────── Gemini writes the answer and cites sources as [1], [2]
        │
 6. Citation check ───── reject unless every citation points at a real source
        │
 { answer, found, sources }  →  chat screen shows the answer and its sources
```

`service.answer()` runs these steps in order. Each step lives in its own file.

---

## Files

### Backend — `backend/app/modules/chat/`

| File | Step | What it does |
|---|---|---|
| `router.py` | — | `POST /api/chat/ask`. Validates the question and returns 503 if the model is not configured. |
| `schemas.py` | — | The API contract: `AskRequest`, `AskResponse`, `Source`. |
| `service.py` | all | Runs the pipeline and builds the response. |
| `sample_documents.py` | 1 | Three fictional documents used until the knowledge module's corpus is connected. |
| `chunking.py` | 1 | `Chunk` and `split_documents()`: splits each section into ≤400-character chunks. |
| `ranking.py` | 2 | Pure algorithms: `tokenize`, `bm25`, `reciprocal_rank_fusion`. |
| `retrieval.py` | 2–3 | `semantic_search`, `keyword_search`, `hybrid_search`, `rerank`. |
| `prompts.py` | 4 | The system prompt and `build_user_prompt()`. |
| `citations.py` | 6 | `check_citations()` and `renumber()`. |

### Shared AI layer — `backend/app/ai/`

All model calls go through this folder (a rule in `CLAUDE.md`), so the provider can change
without touching the modules.

| File | What it does |
|---|---|
| `arabic.py` | `normalize_arabic()`: one normalization for documents and questions alike. |
| `embeddings.py` | `embed_passages()` / `embed_query()` with `multilingual-e5-small`. |
| `reranker.py` | `rerank()` with `bge-reranker-v2-m3`. |
| `llm.py` | `generate()` with Gemini through LangChain. |

### Frontend — `frontend/src/modules/chat/`

| File | What it does |
|---|---|
| `ChatPage.tsx` | The page layout: conversation, question box, sources panel. |
| `useChat.ts` | Conversation state and `ask()`, which calls the backend. |
| `MessageList.tsx` | Messages plus the empty, loading, and error states. |
| `QuestionForm.tsx` | The question box. |
| `SourcesPanel.tsx` | The latest answer's sources, numbered like its citations. |

The request itself is `askQuestion()` in `frontend/src/lib/api.ts`.

---

## Design decisions

**Chunk per section, ≤400 characters, 50 overlapping.** A chunk never mixes two pages,
so every citation names one exact page. The overlap keeps a sentence's context when a
section is split. Splitting uses LangChain's `RecursiveCharacterTextSplitter`, which tries
paragraph, line, sentence, then word boundaries.

**Arabic normalization in one place.** «إجازة», «اجازة», and «إِجَازَة» must look the same to
the search. `normalize_arabic()` removes diacritics and tatweel, unifies alef forms,
ى/ي and ة/ه, and is applied to both documents and questions. It adopts the knowledge
module's more complete rules.

**Hybrid search.** Embeddings understand meaning («من البيت» ≈ «عن بعد») but are weak on
exact terms like «VPN». BM25 is the opposite. Both run, and Reciprocal Rank Fusion merges
their rankings by position, because their scores are on different scales. BM25 is
written by hand (about 20 lines) instead of adding a library. Stop words such as «من»
are ignored; without that, «أبي أشتغل من البيت» matched the access-rights document
because it also contains «من».

**Reranking.** A cross-encoder reads the question and each chunk together, which is far
more accurate than comparing two separate embeddings, but too slow for every chunk. So
the fast search shortlists 10 and the reranker picks the best 3.

**Three chunks for the model.** One is risky: an answer may need two chunks, and the
right one is not always first.

**Grounded prompt.** The model may answer only from the numbered sources, must cite each
fact as `[n]`, and must reply «لا توجد إجابة» otherwise. Retrieved text sits inside
`<sources>` and is declared data, not instructions, to resist prompt injection.

**Citation check.** An answer is accepted only if it cites at least one source and every
cited number exists. One invented citation rejects the whole answer, because an invented
sentence next to a real citation would still look trustworthy. Accepted citations are
renumbered `[1]..[n]` to match the sources shown under the answer.

**Two layers of «not found».** If search finds nothing, the model is never called. If
search finds something irrelevant, the model's «لا توجد إجابة» has no citation, so the
citation check turns it into «ما لقيت».

---

## What the experiments showed

Measured on the sample documents while building the module:

| Question | Before | After |
|---|---|---|
| «أبي أشتغل من البيت» | Meaning search ranked the leave policy first | The reranker puts the remote-work policy first |
| «هل أحتاج VPN؟» | — | Keyword search finds the remote-work policy directly |
| «كم بدل السكن؟» (not in the documents) | Meaning score 0.79, as high as real answers | Reranker scores every chunk 0.0, and the answer is «ما لقيت» |

The small embedding model scores even unrelated text around 0.8, so a similarity
threshold alone cannot tell answerable from unanswerable questions. That is why the
threshold is low (0.70) and the reranker, the model, and the citation check do the real
filtering.

---

## Running and testing

From `backend/`, with `TAMAM_GOOGLE_API_KEY` set in `backend/.env`:

```bash
pip install -e ".[dev,rag]"
uvicorn app.main:app --reload --reload-dir app --port 8000
```

Then open http://localhost:8000/docs and try `POST /api/chat/ask`.

Loading the embedding and reranker models takes from a few seconds to over a minute. Set
`TAMAM_WARM_UP_MODELS=true` in `backend/.env` to load them while the server starts, so
the first question is as fast as the rest. Do this before a demo.

Tests never call a real model; they replace it with `monkeypatch`.

```bash
pytest tests/chat tests/test_ai_arabic.py
```

| Test file | Covers |
|---|---|
| `test_chat_chunking.py` | Chunks keep their source, respect the size limit, and have unique ids. |
| `test_chat_ranking.py` | Tokenizing, BM25, and rank fusion. |
| `test_chat_retrieval.py` | Hybrid merging, the threshold, and reranking. |
| `test_chat_citations.py` | Accepting, rejecting, and renumbering citations. |
| `test_chat_service.py` | The full pipeline, including both «not found» paths. |
| `test_chat_router.py` | The HTTP contract, validation, and the 503 path. |

---

## Next steps

- Answer from the knowledge module's 30 documents instead of `sample_documents.py`, and
  measure accuracy with `data/eval/knowledge_questions.json`.
- Rewrite dialect questions into standard Arabic before searching.
- Stream the answer as it is generated.
