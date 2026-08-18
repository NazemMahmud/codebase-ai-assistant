# What I'd Do With More Time

If I had more time, these are the main improvements I would work on next.

I have listed them roughly in order of value.

## 1. Measure retrieval quality properly

The biggest missing piece is a proper evaluation set.

I would create a small set of questions with known expected results, for example:

```text
Question:
"Where is authentication handled?"

Expected:
app/auth.py
AuthService
```

Then I would add a script such as:

```text
run_eval.py
```

to measure retrieval using metrics like:

* **Hit Rate@K**
* **MRR (Mean Reciprocal Rank)**

Right now, retrieval can be tested manually, but without these metrics it is harder to know whether a change actually improves the system.

A proper evaluation set would also help catch regressions when changing:

* chunking
* embedding models
* search settings
* RRF configuration
* reranking

This would be my first priority.

## 2. Move ingestion to background workers

Repository ingestion currently happens inside the API request.

That means the request stays open while the application:

```text
clones
→ filters
→ chunks
→ creates embeddings
→ stores everything
```

This is fine for a demo, but it becomes a problem with larger repositories.

I would move this work to a background queue using something like:

* Redis + arq
* Redis + Celery

The flow would become:

```text
User starts ingest
        ↓
API creates codebase
        ↓
API returns codebase_id
        ↓
Background worker processes repository
        ↓
Status becomes ready or failed
```

The frontend could check the status while the repository is being processed.

This would remove one of the biggest current scaling and user-experience limitations.

## 3. Stream chat responses

The current chat endpoint waits until the LLM finishes the full answer before returning it.

I would add streaming using:

```text
Server-Sent Events (SSE)
```

This would allow the frontend to show the response as it is generated.

It would not necessarily make the LLM itself faster, but it would make the application feel much more responsive.

This was mainly left out because of time.

### Persist chat history

Chat history is currently kept only in the frontend, in memory. It survives while the
page is open but is lost on a refresh or when a different repository is selected.

I would store conversations in the database — for example a `conversations` table and a
`messages` table (role, content, citations, `codebase_id`, timestamp) — and load a
repository's history when it is selected. History would then survive refreshes, server
restarts, and different devices.

### Support multi-turn conversation

Each `/api/chat` call is currently independent: previous questions are not sent to the
model, so it behaves as single-turn Q&A rather than a real chat. A follow-up like
"and the second one?" cannot resolve, because neither the prompt nor the retrieval step
sees the earlier turns.

With stored history I would make the chat conversational:

* include recent turns in the prompt so the model has context
* use the history to rewrite the retrieval query (history-aware retrieval), so a
  follow-up question is expanded with what the conversation was about before searching

Persisting history (above) is the prerequisite for both.

## 4. Add incremental re-indexing

Right now, re-indexing a repository means processing the whole repository again.

That includes creating embeddings for files that may not have changed.

A better approach would store:

```text
commit_sha
```

for the repository and something like:

```text
content_hash
```

for each file.

Then the system could compare the new version with the previous one.

The flow could be:

```text
unchanged files → keep existing chunks and embeddings
changed files   → re-chunk and re-embed
new files       → chunk and embed
deleted files   → remove old chunks
```

This would save a lot of processing time and embedding cost for large repositories.

I would probably introduce a separate `files` table to support this cleanly.

## 5. Improve retrieval quality

There are several retrieval improvements I would like to test.

### Add a reranker

After vector, full-text, and trigram results are combined with RRF, I would add a **cross-encoder reranker**.

The flow would become:

```text
Vector + FTS + Trigram
        ↓
       RRF
        ↓
Cross-encoder reranker
        ↓
Best final chunks
```

A reranker can look at the question and each retrieved chunk together and produce a better final ordering.

### Improve JavaScript and TypeScript chunking

The current Tree-sitter chunker handles the main structures, but there are some JavaScript and TypeScript patterns I would improve.

For example:

```javascript
const processPayment = () => {
  ...
}
```

and TypeScript type aliases.

These should be recognized as useful symbols and chunked properly.

### Reduce class and method overlap

Currently, a class chunk can overlap heavily with chunks created for its individual methods.

I would improve this by storing a smaller class-level chunk, such as the class header and important metadata, instead of repeating the whole class body.

This would reduce duplicate content in retrieval results.

### Make chunk sizes token-aware

The fallback logic currently works mostly with lines and character limits.

I would make chunk splitting token-aware so very large functions or classes are split safely before reaching model limits.

This would be better than silently truncating oversized code.

## 6. Improve observability

The project already has logging, but I would add more production-friendly monitoring.

### Structured logs

I would use JSON logs with information such as:

```text
request_id
trace_id
codebase_id
endpoint
duration
status
```

This would make production debugging much easier.

### RAG and LLM metrics

I would also track metrics such as:

* retrieval latency
* LLM latency
* total request time
* number of retrieved chunks
* retrieval scores
* input tokens
* output tokens
* tokens per query

For deeper LLM tracing, I would consider adding something like Langfuse.

## 7. Improve robustness

There are a few smaller improvements that would make the system safer and more reliable.

### Prevent duplicate repositories

I would normalize repository URLs and add a database constraint such as:

```sql
UNIQUE(location) WHERE deleted_at IS NULL
```

This would guarantee that only one active codebase exists for the same repository.

### Add clone timeout and size checks

Repository cloning should have a timeout so a bad or very slow clone cannot run forever.

I would also check repository size through the GitHub API before cloning when possible.

This would allow very large repositories to be rejected earlier.

### Clean up soft-deleted data

The project uses soft deletes, so old chunks remain in the database.

I would add a scheduled cleanup job to permanently remove old deleted records after a retention period.

### Harden SSRF against DNS rebinding

The URL check resolves the host at validation time, but `git clone` resolves DNS again later.

A rebinding attack could point the second lookup at an internal address.

I would resolve the host once and clone against the pinned IP, or enforce egress restrictions at the network level.

### Clean up leaked temp directories

The temporary clone directory is removed in a `finally` block, but a process kill or OOM mid-ingest can leave it behind and slowly fill disk.

I would add a startup/periodic sweep that removes stale ingest temp directories by age.

### Surface the failure reason

A failed ingest sets `status=failed`, but the reason only lives in `error_logs`, so the API response alone does not explain it.

I would expose the latest error for a codebase through the status endpoint (joined on `codebase_id`), or store a short reason on the row.

## 8. Support more repository sources and languages

The current version only accepts public GitHub repositories.

I would extend the loader to support:

* ZIP uploads
* local folders
* private GitHub repositories
* a specific branch, tag, or commit (only the default branch is indexed today)
* more Git providers if needed

For private repositories, users could provide a token or connect through a GitHub App.

I would also add more Tree-sitter grammars so more programming languages get structure-aware chunking instead of falling back to line-based splitting.

## 9. Add multi-user support and production hardening

The current project is designed as a simple single-user application.

For a real hosted product, I would add:

* authentication
* authorization
* repository ownership
* per-user data isolation
* rate limits
* usage quotas
* secret management
* proper CI/CD

Ingesting repositories can be expensive, so rate limits and quotas would be especially important.

I would also move API keys and other secrets into a proper secrets manager instead of relying on local `.env` files.

## Tests I would add

The current tests focus on the most important retrieval logic, but I would add more coverage in a few areas.

### Database-backed retrieval (integration) tests

The current suite is unit-only (`test_chunking.py`, `test_fusion.py`). The biggest gap
is running the real searches against a throwaway PostgreSQL instance and asserting on
behavior that only appears with a live database:

* vector, full-text, and trigram search ranking
* codebase scoping (results stay within one codebase)
* soft-delete exclusion (`deleted_at IS NULL`)

I would set this up with a disposable Postgres container fixture so retrieval is
verified end-to-end, not just the pure-Python pieces.

### Context assembly tests

I would test things such as:

* token-budget limits
* which chunks are included
* whether chunks are kept whole
* citation formatting

### Loader tests

I would add more tests for:

* SSRF protection
* invalid repository URLs
* private/internal addresses
* file filtering
* binary files
* secret files
* repository limits

### API endpoint tests

I would add endpoint-level tests for:

```text
POST /api/ingest
POST /api/chat
```

External parts such as Git cloning and the LLM could be mocked so the API behavior can be tested without making real network requests.

### Retrieval regression tests

The evaluation set from the first section could also be run as part of automated testing.

That would make it possible to detect when a code change unexpectedly makes retrieval worse.

## Overall priority

If I had to choose only a few next steps, I would focus on:

```text
1. Retrieval evaluation
2. Background ingestion
3. Incremental re-indexing
4. Better retrieval + reranking
5. Production monitoring
```

The current version proves the main RAG flow, but these changes would make it easier to measure, scale, and operate as a real application.
