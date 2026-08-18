# Engineering Standards

This document explains the engineering practices I followed in the project, along with a few things I intentionally left out because of the limited time.

## Standards I followed

### Keep API routes small

The API routes are kept simple.

Their main jobs are to:

* receive the request
* validate the input
* call the correct service
* convert application errors into HTTP responses

The main business logic lives inside service classes and functions instead of inside the routes.

This also makes the same logic reusable later from places such as a background worker.

### Keep responsibilities separated

Different parts of the application are split into separate modules.

For example:

```text
ingest
chunking
retrieval
chat
llm
embedding
```

Each module focuses on one main responsibility.

The modules also expose only the parts that other parts of the application need, while internal helpers stay private.

This keeps the codebase easier to understand and change.

### Avoid unnecessary hard-coded values

Values that may be reused or changed are kept in constants or configuration files instead of being repeated throughout the code.

Examples include:

* allowed hosts
* file filtering rules
* response messages
* database settings
* table names
* prompts

For example, table names come from a shared `TableName` definition instead of being written differently in multiple places.

This reduces duplication and makes changes safer.

### Validate data at the boundaries

API request and response models use Pydantic.

This gives:

* input validation
* clear request/response structures
* automatic `422` responses for invalid input
* automatic OpenAPI documentation

Database models also use typed SQLAlchemy models.

This helps catch mistakes earlier and makes the expected data structure clearer.

### Version database changes

All database schema changes are handled through Alembic migrations.

For example:

```text
extensions
→ tables
→ indexes
→ later schema changes
```

The database schema is not manually changed as part of normal development.

Migrations are also kept independent from application logic as much as possible.

This makes database changes:

* repeatable
* reviewable
* easier to deploy
* easier to understand later

### Use the same API response format

All endpoints return the same basic structure:

```json
{
  "success": true,
  "message": "",
  "data": {}
}
```

Keeping one response format makes the API easier for the frontend and API users to work with.

### Build safety into the normal flow

Some safety rules are part of the default application behavior.

For repository ingestion, the application:

* validates GitHub URLs
* protects against SSRF
* filters binary files
* filters likely secret files
* limits repository size and file count
* never executes code from the repository

For RAG and chat:

* retrieved source code is treated as untrusted data
* code is separated from LLM instructions
* the model is told not to follow instructions found inside source code or comments
* the model returns a clear not-found response when the answer is not available

The aim is to avoid relying on users or developers to remember these protections each time.

### Keep results reasonably reproducible

Dependency versions are pinned.

The LLM model is also configured explicitly rather than selected automatically.

A low temperature is used for generation.

This helps make answers more consistent when testing and evaluating the system.

LLM output is never perfectly deterministic, but these choices reduce unnecessary variation.

### Keep documentation close to the code

I documented important decisions while building the project.

This includes:

* architecture
* design decisions
* ingestion flow
* retrieval flow
* chat flow
* known limitations
* future improvements

This is useful because the reason behind a decision can otherwise be easy to forget later.

### Test the parts where mistakes matter most

I focused testing on logic where a small bug could have a large effect on the final RAG result.

The current version keeps only unit tests (`test_chunking.py`, `test_fusion.py`),
covering areas such as:

* chunk boundaries
* language detection
* RRF calculations

The goal was not to get a high coverage percentage just for the number, but to test the parts that have the biggest effect on correctness.

Database-backed integration tests for retrieval are a planned next step (see below).

## Things I intentionally skipped

Some engineering practices would be useful in a larger or production-ready version, but I left them out of this first version to keep the scope realistic.

### Full test coverage and CI

The project has unit tests for the highest-value areas, but it does not have complete test coverage.

The main gap is **database-backed integration tests** for retrieval — running the
real vector, full-text, and trigram searches against a throwaway PostgreSQL instance
and asserting on ranking, codebase scoping, and soft-delete exclusion. These would be
added with a test database fixture (e.g. a disposable Postgres container) so retrieval
is verified end-to-end, not just the pure-Python pieces (chunking, fusion).

There is also no CI pipeline or minimum coverage requirement yet.

A production version should add something like:

```text
push / pull request
      ↓
run tests
      ↓
run linting
      ↓
check migrations
      ↓
build
```

This was left out mainly because of the project time limit.

### Async database access

The project currently uses:

```text
SQLAlchemy + psycopg 3
```

in synchronous mode.

I considered async database access, but the current application spends more time on embedding, retrieval, and LLM calls than on database I/O.

So adding async database code would increase complexity without solving the main current bottleneck.

The database layer is kept separate enough that moving to async later should be a focused change.

### Automatic formatter and linter checks

The code is kept formatted and unnecessary `# noqa` comments were removed.

However, tools such as:

```text
ruff
black
```

are not currently enforced through pre-commit hooks or CI.

In a team or production project, I would add these so formatting and linting are checked automatically instead of depending on developers to run them manually.

### Background processing

Repository ingestion currently happens inside the API request.

That is acceptable for the first version, but it is not ideal for large repositories.

The production version should use:

```text
API
→ queue
→ background worker
→ indexing
```

The service structure already makes this change easier, but the actual queue and worker were left out of this version.

### Detailed metrics and tracing

The application currently has:

* structured logging
* rotating log files
* an `error_logs` database table

What it does not yet have is detailed RAG and LLM monitoring.

Useful future metrics would include:

* retrieval time
* LLM latency
* total request time
* tokens per request
* retrieval scores
* number of chunks used
* failed requests

LLM tracing with a tool such as Langfuse could also be added later.

### Golden retrieval evaluation

I planned to create a fixed evaluation set where questions have known expected files or symbols.

That would allow retrieval to be measured using metrics such as:

```text
Hit Rate@K
MRR
```

This was not completed in the current time box.

It would be one of the first things I would add next because it would make retrieval improvements measurable instead of relying only on manual checking.

### Authentication and multi-tenancy

The current project is designed as a simple single-user application.

It does not currently include:

* user authentication
* authorization
* organization support
* repository ownership
* rate limiting
* usage quotas

Those are important for a real public service, but they do not directly improve the main RAG and retrieval problem this version was built to demonstrate.

They are therefore left for a production version.

## Overall approach

The main principle I followed was:

> A solid, well-engineered basic solution is better than adding complexity just for the sake of it.

The goal was to build the important parts properly:

```text
ingest
→ chunk
→ embed
→ retrieve
→ build context
→ generate a grounded answer
```

For features that were not necessary for the first version, I tried to keep clear extension points and document what should be added next rather than partially building everything.
