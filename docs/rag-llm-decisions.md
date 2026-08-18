# RAG / LLM Approach & Decisions

This document explains the main RAG and LLM choices made for this project and why I chose them.

Other architecture and database decisions, such as UUIDv7 IDs, sync vs async database access, using one datastore, and soft deletes, are covered in [project-approach.md](project-approach.md#design-decision-records).

## Chunking

### Options considered

I looked at a few ways to split source code into chunks:

* fixed-size text chunks
* structure-aware chunking using Tree-sitter
* LLM-based semantic chunking

### Chosen approach

For Python, JavaScript, and TypeScript, I use **Tree-sitter** to understand the code structure.

The goal is to create chunks around real code blocks such as:

* functions
* classes
* methods

Each chunk also keeps useful metadata such as:

* symbol name
* symbol type
* start line
* end line

For other languages, or files where Tree-sitter cannot find useful definitions, the project falls back to a simple line-based splitter:

```text
200 lines per chunk
20 lines overlap
```

### Why

Fixed-size splitting is simple, but it can cut a function or class in the middle.

For example:

```text
Chunk 1 → first half of a function
Chunk 2 → second half of the same function
```

That makes retrieval harder and can also make citations less useful.

Using real code boundaries gives cleaner chunks and better `file:line` references.

The fallback splitter makes sure files can still be indexed even when structure-aware chunking is not available.

## Embedding model

### Options considered

I considered:

* hosted embedding APIs such as OpenAI or Cohere
* general local embedding models such as `bge-small` and `bge-base`
* a code-focused local embedding model

### Chosen approach

The project uses:

```text
jinaai/jina-embeddings-v2-base-code
```

It creates:

```text
768-dimensional embeddings
```

and runs locally through `sentence-transformers`.

### Why

The model is designed for code, so it should work better with things like:

* function names
* classes
* programming-related text
* code structure

Another important reason is that embeddings run locally.

This means repository ingestion and retrieval do not require an external API key.

Only the final chat generation step needs an LLM API.

The main trade-off is that the model adds extra local dependencies and makes ingestion more CPU-heavy.

It also requires:

```text
trust_remote_code
einops
```

The embedding size is fixed at `768` in the application configuration and database schema so everything stays consistent.

## Vector database

### Options considered

I considered using a dedicated vector database such as:

* Pinecone
* Qdrant
* Weaviate

I also considered storing vectors directly in PostgreSQL using pgvector.

### Chosen approach

The project uses:

```text
PostgreSQL + pgvector
```

Vector search uses an HNSW index with cosine similarity.

### Why

This keeps everything in one database:

```text
repository metadata
code chunks
embeddings
full-text search
trigram search
```

That makes the system easier to develop and operate.

It also allows the retrieval logic to combine vector and normal PostgreSQL search in the same place.

A separate vector database could still be introduced later if the project becomes large enough to need it.

## Retrieval

### Options considered

I considered:

* vector search only
* keyword search only
* hybrid search
* hybrid search with an additional reranker

### Chosen approach

The project uses three search methods together:

1. **Vector search** using pgvector
2. **Full-text search** using PostgreSQL `tsvector`
3. **Trigram search** using `pg_trgm` on `symbol_name`

The results are then combined using:

```text
Reciprocal Rank Fusion (RRF)
```

### Why

Different searches are good at different things.

Vector search is useful when the question is based on meaning.

For example:

```text
Where is payment processing handled?
```

But it may miss an exact code identifier such as:

```text
processPayment
```

Keyword and trigram search are better for exact names, but they can miss questions written in different words.

Using both helps cover both cases.

The flow looks like this:

```text
Question
   ↓
┌───────────────┐
│ Vector search │
├───────────────┤
│ Full-text     │
├───────────────┤
│ Trigram       │
└───────┬───────┘
        ↓
       RRF
        ↓
Best combined results
```

RRF combines rankings based on the result positions rather than the raw scores.

This is useful because the three search methods produce very different score types:

```text
cosine similarity
ts_rank
trigram similarity
```

Trying to compare those scores directly would be difficult.

A cross-encoder reranker could improve retrieval further, but I left that for a later version.

## Orchestration framework

### Options considered

I considered using:

* LangChain
* LangGraph
* a small custom pipeline

### Chosen approach

The project does not use a RAG orchestration framework.

The flow is written directly in the application:

```text
question
→ create embedding
→ search
→ combine results
→ build context
→ send to LLM
→ return answer
```

### Why

The flow in this project is fairly simple and linear.

Keeping it as normal Python services makes it easier to:

* understand
* debug
* test
* change
* explain during review

It also keeps the retrieval logic visible instead of hiding important steps behind a framework.

If the application later needs more complex workflows, tools, branching, or agents, a framework could be introduced then.

## LLM for answer generation

### Options considered

I considered:

* directly using one specific LLM SDK
* adding a small provider interface so the provider can be changed later

### Chosen approach

The project uses an:

```text
LLMProvider
```

interface.

The current implementation uses OpenRouter through its OpenAI-compatible API.

Users provide their own API key.

The model is configured through:

```env
LLM_MODEL=...
```

and the temperature is kept low:

```text
0.1
```

### Why

The provider interface keeps the application independent from one LLM company.

Another OpenAI-compatible provider can be added later without changing the main chat flow.

Using a user-provided key also keeps API keys out of the source code.

The model is fixed in configuration instead of automatically selected.

This makes testing and comparing answers more consistent.

The low temperature also helps keep answers more predictable.

Only the final answer generation uses a large language model.

The rest of the RAG pipeline runs locally.

## Prompt and context handling

After retrieval, the selected chunks are added to the prompt as context.

The application uses a configurable token budget:

```text
CONTEXT_TOKEN_BUDGET
```

The current implementation estimates token usage using roughly:

```text
4 characters ≈ 1 token
```

Whole chunks are added until the budget is reached.

Chunks are not cut in the middle just to fit the prompt.

This keeps the source code easier for the model to understand.

Each chunk is labelled with information such as:

```text
[1] app/auth.py:12-40 (class AuthService)
```

This gives the model enough information to return useful citations.

### Grounding prompt

The system prompt tells the model to:

* answer only from the provided code
* include `file:line` references
* avoid making up files, functions, or behavior

If the answer cannot be found in the retrieved code, the model is instructed to return exactly:

```text
Not found in the indexed codebase.
```

## Guardrails

A few protections are included to make both ingestion and chat safer.

### Answer only from retrieved code

The LLM is instructed to use only the provided context.

This reduces the chance of inventing code that does not exist in the repository.

### Code is treated as data

Repository files may contain comments or strings that look like instructions to an LLM.

For example:

```text
Ignore previous instructions and...
```

The application treats retrieved source code as data, not as instructions.

The system prompt tells the model to ignore instructions found inside code or comments.

This is a basic protection against prompt injection from repository content.

### Safe repository ingestion

Repository URLs are checked before cloning.

Current protections include:

* only allow `https`
* only allow GitHub URLs
* reject URLs containing credentials
* reject private, local, loopback, and reserved IP addresses
* limit repository size
* limit file count
* ignore binary files
* ignore likely secret files
* never execute repository code
* do not follow symlinks outside the repository

### Clear failure behavior

The application avoids creating an answer when something important is missing.

For example:

```text
Codebase does not exist
→ 404
```

```text
Codebase is still indexing
→ return its current status
```

```text
No useful chunks found
→ "Not found in the indexed codebase."
```

```text
LLM request fails
→ 502
```

This is better than trying to guess an answer.

## Quality controls

Tests focus on the parts where small mistakes could change retrieval results.

### Unit tests

Unit tests cover things such as:

* language detection
* chunk boundaries
* Tree-sitter chunking behavior
* RRF ranking calculations

Only unit tests are kept in the current version (`test_chunking.py`, `test_fusion.py`).
Database-backed integration tests for retrieval (vector / full-text / trigram search,
codebase filtering, soft-delete exclusion) were planned but not included in this slice.

### Current gap

One thing I did not complete was a proper retrieval evaluation dataset.

A better evaluation setup would include a list of questions with known correct files or chunks and calculate metrics such as:

```text
Hit Rate@K
MRR
```

This would make it easier to compare retrieval changes with real numbers instead of only manual testing.

More details are in:

[`what-id-do-differently.md`](what-id-do-differently.md)

## Observability

The application currently has logging across the main layers.

Logs are written to:

* the console
* rotating log files

Important application failures are also stored in the:

```text
error_logs
```

table.

An error record can include:

* component
* exception type
* error message
* traceback
* extra context
* related codebase

The error logger uses its own database session.

This means the error can still be saved even if the main request transaction later fails and rolls back.

### Not added yet

I would also like to track per-request RAG and LLM metrics such as:

* retrieval time
* LLM response time
* total request time
* number of retrieved chunks
* tokens sent to the LLM
* tokens returned by the LLM

A tracing tool such as Langfuse could also be added later for deeper LLM debugging.

These were left out of the current version to keep the first implementation focused.
