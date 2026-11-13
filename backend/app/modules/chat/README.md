# Chat module — «اسأل عن إجراء»

Owner: Amira (`Amira-K-Alsaif`)

An employee asks a question in Arabic, including Saudi dialect. Tamam answers **only
from the company's documents**, shows **where each fact came from**, and says
**«ما لقيت»** when the documents don't contain the answer, instead of guessing.

This is Retrieval-Augmented Generation (RAG): find the right passages first, then let a
language model write the answer from those passages alone.

**Result:** on the team's 50 evaluation questions, the right document is among the three
passages the model reads for **48 of 50 (96%)**, and ranked first for 44 (88%).

---

## How a question is answered

```
"أبي أشتغل من البيت"
        │
 1. Corpus ───────────── the knowledge module's chunks, each knowing its document and section
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
| `router.py` | — | `POST /api/chat/ask`. Validates the question, and returns 503 when the service is not set up or the model's quota is used up. |
| `schemas.py` | — | The API contract: `AskRequest`, `AskResponse`, `Source`. |
| `service.py` | all | Runs the pipeline and builds the response. |
| `corpus.py` | 1 | `Chunk` and `load_chunks()`: reads the chunks the knowledge module prepared. |
| `ranking.py` | 2 | Pure algorithms: `tokenize`, `bm25`, `reciprocal_rank_fusion`. |
| `retrieval.py` | 2–3 | `semantic_search`, `keyword_search`, `hybrid_search`, `rerank`. |
| `prompts.py` | 4 | The system prompt and `build_user_prompt()`. |
| `citations.py` | 6 | `check_citations()` and `renumber()`. |
| `evaluate.py` | — | Measures retrieval and answers on `data/eval/knowledge_questions.json`. |

### Shared AI layer — `backend/app/ai/`

All model calls go through this folder (a rule in `CLAUDE.md`), so the provider can change
without touching the modules.

| File | What it does |
|---|---|
| `arabic.py` | `normalize_arabic()`: one normalization for documents and questions alike. |
| `embeddings.py` | `embed_passages()` / `embed_query()` with `multilingual-e5-small`. |
| `reranker.py` | `rerank()` with `bge-reranker-v2-m3`. |
| `llm.py` | `generate()` with Gemini through LangChain. Turns a used-up quota into `LLMUnavailableError`. |

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

**Read the knowledge module's chunks; don't re-split.** Ingestion belongs to the knowledge
module (Gamar): it splits the 28 company documents by heading into 88 chunks and writes
`data/processed/chunks.jsonl`. The chat reads that file and the manifest, so the two
modules share the Chunk contract from `docs/team.md`, not code.

**Search with titles, cite with text.** Many chunks are one short sentence that does not
say what it is about, such as «المدة المتوقعة ثلاثة أيام عمل». Search reads
`Chunk.search_text`, the chunk prefixed with its document and section titles. This one
change raised retrieval from 84% to 96% on the evaluation questions. Citations still quote
only the chunk's own text.

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

On the 50 evaluation questions (`python -m app.modules.chat.evaluate`):

| Version | Right document ranked first | Right document in the top 3 |
|---|---|---|
| Chunk text only | 41 (82%) | 42 (84%) |
| With document and section titles | 44 (88%) | **48 (96%)** |

The two remaining misses are a question about recording attendance, and a question about
a suspicious link that retrieved the phishing guide instead of the information-security
policy, which is a reasonable answer too.

Earlier experiments on three sample documents:

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

First prepare the knowledge module's chunk file, which the chat reads:

```bash
python -m app.modules.knowledge.cli
```

Then open http://localhost:8000/docs and try `POST /api/chat/ask`.

Gemini's free tier allows only about 20 answers per day per model. When the quota is used
up, the chat shows «خدمة الإجابة غير متاحة حالياً». For a demo, keep a spare key or enable
billing.

Loading the embedding and reranker models takes from a few seconds to over a minute. Set
`TAMAM_WARM_UP_MODELS=true` in `backend/.env` to load them while the server starts, so
the first question is as fast as the rest. Do this before a demo.

Tests never call a real model; they replace it with `monkeypatch`.

```bash
pytest tests/chat tests/test_ai_arabic.py tests/test_ai_llm.py
python -m app.modules.chat.evaluate            # retrieval accuracy, no Gemini calls
python -m app.modules.chat.evaluate --answers  # also checks Gemini's answers (uses quota)
```

| Test file | Covers |
|---|---|
| `test_chat_corpus.py` | Reading chunks with their titles, and the message when the file is missing. |
| `test_chat_ranking.py` | Tokenizing, BM25, and rank fusion. |
| `test_chat_retrieval.py` | Hybrid merging, the threshold, and reranking. |
| `test_chat_citations.py` | Accepting, rejecting, and renumbering citations. |
| `test_chat_service.py` | The full pipeline, including both «not found» paths. |
| `test_chat_router.py` | The HTTP contract, validation, and the 503 paths. |
| `test_chat_warm_up.py` | Loading the models at startup when enabled. |

---

## Next steps

- Measure the answers themselves with `evaluate --answers` once there is enough quota.
- Rewrite dialect questions into standard Arabic before searching.
- Stream the answer as it is generated.
