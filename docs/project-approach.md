# Project Approach

## Why I chose this option

There were four options, and all of them involved some kind of retrieval problem.

I chose this project because working with source code creates a few extra challenges that are interesting to solve.

For example:

* code should not be split randomly in the middle of a function
* search needs to understand meaning
* search also needs to find exact names such as functions, classes, and variables
* answers should point back to the correct file and line numbers

Because of that, this option gave me a good chance to focus on both normal backend engineering and RAG-specific decisions.

## Main idea

My main approach was simple:

> Build a small solution that works well before adding more complexity.

I wanted the first version to prove the most important parts of the system, especially:

* code chunking
* retrieval quality
* grounded answers with citations

Instead of trying to build every possible feature, I kept the first version focused and left clear places where more features can be added later.

## Scope of the first version

The first version includes:

* public GitHub repositories only
* Tree-sitter chunking for Python, JavaScript, and TypeScript
* a simple text-based fallback chunker for other files
* local embeddings
* PostgreSQL with pgvector
* hybrid retrieval using vector search, full-text search, and trigram search
* Reciprocal Rank Fusion (RRF) to combine search results
* synchronous chat
* one LLM provider through OpenRouter
* user-provided API key
* grounded answers with file and line citations
* a small React frontend

Some features were intentionally left out of the first version.

For example:

* ZIP upload
* local folder upload
* background ingestion workers
* multiple LLM providers
* private GitHub repositories

These can be added later without changing the main retrieval design.

## How I approached the work

### 1. Design before coding

I started by writing down the main architecture and important technical decisions.

This helped me think about questions such as:

* How should code be split?
* Where should embeddings be stored?
* How should exact function names be found?
* Should the application use a RAG framework?
* Should database access be sync or async?

Writing these decisions down first made the implementation more consistent.

It also made it easier to explain why each technology was chosen.

### 2. Build one part at a time

I divided the work into smaller vertical steps.

The branch flow was roughly:

```text id="njfhwh"
feat/1 skeleton
→ feat/2 ingest
→ feat/3 chunking
→ feat/4 embed + store
→ feat/5 retrieval
→ feat/6 context + LLM
→ feat/7 chat
→ feat/8 codebases API
→ feat/9 frontend
```

Each step added one usable part of the system.

This made the project easier to review and reduced the chance of mixing too many changes together.

### 3. Keep future changes easy

For some parts, I deliberately built a simple version first but kept the code structured so it can be improved later.

For example:

* database access is synchronous now, but the DB layer can be changed to async later
* there is only one LLM provider now, but it sits behind an `LLMProvider` interface
* the chunking logic uses a common interface, so support for more languages can be added later
* ingestion is synchronous now, but the service can later be called from a background worker

The idea was to avoid building unnecessary infrastructure now while also avoiding code that would need a complete rewrite later.

### 4. Document decisions while building

I added documentation during development instead of leaving everything until the end.

This includes:

* architecture notes
* ingestion flow
* retrieval flow
* chat flow
* database decisions
* limitations
* future improvements

This makes it easier to understand both what the system does and why it was built this way.

### 5. Test the risky parts

I focused tests on the parts where small mistakes could have a large effect on retrieval quality.

For example:

* language detection
* chunk boundaries
* Tree-sitter behavior
* RRF ranking calculations

These are more important to test carefully because mistakes here can directly affect which code is shown to the LLM.

## Trade-offs I made

A few decisions were made mainly to keep the first version simple and understandable.

### Synchronous ingestion and chat

The current ingestion and chat flows are synchronous.

This makes the application simpler and easier to demonstrate.

The downside is that large repositories can keep an API request open for a long time.

For production, ingestion should move to a queue and background worker.

That next step is covered in [productionization.md](productionization.md).

### Synchronous database access

The project uses synchronous SQLAlchemy with psycopg 3.

I considered using an async database setup, but I did not think it was necessary for this version.

A large part of the request time is spent on:

```text id="atbpph"
embedding
retrieval
LLM generation
```

rather than waiting for many small database queries.

So synchronous database code keeps the implementation simpler without solving a major current bottleneck.

If database concurrency becomes a problem later, the engine and session layer can be changed to async.

### pgvector instead of a separate vector database

I chose PostgreSQL with pgvector instead of adding something like Pinecone, Qdrant, or Weaviate.

For this project, keeping everything in one database is simpler.

PostgreSQL can handle:

* repository metadata
* code chunks
* embeddings
* full-text search
* trigram search

This avoids having to keep data synchronized between two separate databases.

A dedicated vector database could still make sense at a much larger scale.

### No RAG orchestration framework

I decided not to use LangChain or LangGraph.

The current pipeline is simple:

```text id="6nwzag"
question
→ embedding
→ retrieval
→ RRF
→ context
→ LLM
→ answer
```

Writing this directly as normal services makes the logic easy to follow.

It also keeps the retrieval implementation visible, which is one of the important parts of this project.

## Design decisions

The following sections explain some of the main database and architecture decisions.

RAG-specific decisions such as chunking, embeddings, retrieval, and LLM choices are documented separately in:

[rag-llm-decisions.md](rag-llm-decisions.md)

## Primary keys: UUIDv7

### Options considered

I considered:

* auto-increment `bigint`
* UUIDv4
* UUIDv7

### Chosen approach

The project uses:

```text id="62r4am"
UUIDv7
```

generated by PostgreSQL.

PostgreSQL 18 provides the native:

```text id="d82k9f"
uuidv7()
```

function, which is used as the default value for IDs.

### Why

UUIDv7 has a useful combination of features.

It is globally unique like other UUIDs, but it is also ordered by time.

This means newly created IDs are usually close together in a database index.

That gives better B-tree index behavior than completely random UUIDv4 values.

UUIDs are also useful because they:

* can safely be exposed in API URLs
* do not directly reveal how many database rows exist
* work well if data is later split between multiple databases or services

### Trade-off

The current setup depends on PostgreSQL 18's native `uuidv7()` support.

On older PostgreSQL versions, UUIDv7 would need to be generated using an extension or inside the application.

## Database access: synchronous

### Options considered

I considered:

* async SQLAlchemy with asyncpg
* synchronous SQLAlchemy with psycopg 3

### Chosen approach

The project uses:

```text id="85dnmc"
SQLAlchemy + psycopg 3
```

in synchronous mode.

### Why

The main goal was to keep the database layer simple.

The current workload is not heavily database-bound.

More time is normally spent on:

* embedding
* retrieval processing
* LLM calls

Because of that, moving to async database access would add complexity without giving much benefit for this version.

Another reason for choosing psycopg 3 is that it also supports async usage.

So there is still a clear upgrade path if the application needs more database concurrency later.

### Trade-off

For a high-traffic system with many simultaneous database operations, async database access could perform better.

If that becomes necessary, most of the change should stay inside the database engine and session layer.

## One datastore: PostgreSQL + pgvector

### Options considered

I considered using:

```text id="nhk7br"
PostgreSQL + separate vector database
```

with services such as:

* Pinecone
* Qdrant
* Weaviate

I also considered keeping everything inside PostgreSQL using pgvector.

### Chosen approach

The project uses:

```text id="xupvpb"
PostgreSQL + pgvector
```

for all application data.

This includes:

* codebase information
* chunks
* embeddings
* full-text search
* trigram search

### Why

For this size of application, using one database keeps things much simpler.

For example, storing a chunk and its embedding can happen in the same database transaction.

Hybrid retrieval can also run without having to call and combine data from two different systems.

The architecture is therefore easier to:

* run locally
* debug
* deploy
* maintain

The retrieval-specific reasons are covered in more detail in:

[rag-llm-decisions.md](rag-llm-decisions.md)

### Trade-off

A dedicated vector database may provide more features and better scaling for very large vector datasets.

If this project grows enough to need that, the vector search layer could be moved later.

## Deletes: soft delete

### Options considered

I considered:

* permanently deleting rows
* soft deleting rows using a `deleted_at` field

### Chosen approach

The project uses soft deletes.

Instead of immediately removing a record, it gets a timestamp in:

```text id="e6suka"
deleted_at
```

Normal queries only use rows where:

```sql id="eh231u"
deleted_at IS NULL
```

### Why

Soft deletes are useful when re-indexing a repository.

Imagine the repository already has 500 chunks.

During re-ingestion, the application needs to replace those chunks with a new set.

The flow can be:

```text id="t45n0y"
old chunks
→ soft delete
→ insert new chunks
→ commit transaction
```

If the new indexing process fails before the transaction is completed, the database does not have to be left in a half-finished state.

Soft deletes also provide some history that can help with recovery or debugging.

### Trade-off

Soft-deleted records still take database space.

Over time, the database can grow with old codebase and chunk records.

A production version should run a scheduled cleanup job that permanently deletes old records after a chosen retention period.

This is covered in:

[productionization.md](productionization.md)

## What I would validate next

The next thing I would add is a proper retrieval evaluation set.

The idea would be to create a set of questions with known expected results.

For example:

```text id="1zltmf"
Question:
"Where is authentication handled?"

Expected:
app/auth.py
AuthService
```

Then retrieval quality could be measured using metrics such as:

```text id="kyia5g"
Hit Rate@K
MRR
```

That would make it possible to compare changes to:

* chunking
* embedding models
* search settings
* RRF configuration
* reranking

using real numbers instead of only manually checking whether the results look good.

This is the first improvement I would focus on with more time.

See:

[what-id-do-differently.md](what-id-do-differently.md)
