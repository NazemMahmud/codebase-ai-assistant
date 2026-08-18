# Productionizing, Scaling & Deployment

The current version is built as a simple, single-machine project.

That is fine for development and demos, but a real production system would need a few changes to handle:
* larger repositories
* more users
* more API requests
* longer indexing jobs
* better reliability
* better security and monitoring, etc.

This document explains the main improvements I would make before running the project at scale on platforms such as AWS, GCP, Azure, or Cloudflare.

## Make repository ingestion asynchronous

This is probably the most important change.

Right now: `POST /api/ingest`

does everything inside the same API request:
```text
clone
→ filter files
→ chunk code
→ create embeddings
→ save to database
```

This works for small repositories, but larger repositories can take much longer.

That means the request may stay open for too long or eventually time out.

A better production flow would be:

```text
User starts ingest
        ↓
API creates a job
        ↓
API returns immediately
        ↓
Background worker picks up the job
        ↓
Clone repository
        ↓
Chunk + embed + store
        ↓
Update codebase status to ready
```

The `/ingest` endpoint could return:

```text
202 Accepted
```

with the `codebase_id`.

The frontend could then check the codebase status until indexing finishes.

A queue could be implemented with tools such as:

* Redis + arq
* Redis + Celery
* AWS SQS, etc.

The current ingestion logic is already separated from the web/API layer.

That means a background worker could reuse the existing `ingest_repository` service instead of creating a completely different ingestion flow.

The existing `pending` status would also become useful:

```text
pending → indexing → ready
                   ↘ failed
```

## Database

For production, I would use a managed PostgreSQL service that supports pgvector.

Examples include:

* AWS RDS / Aurora
* Azure Database for PostgreSQL, etc.

Using a managed database reduces the amount of database maintenance needed.

### Connection pooling

As the number of API requests grows, opening too many database connections can become a problem.

A connection pooler such as: `PgBouncer` or `RDS Proxy`

can help manage those connections.

The application currently uses synchronous SQLAlchemy with psycopg 3.

That should be enough for the current workload because a large part of the request time is spent on retrieval and LLM calls rather than database work.

If database concurrency becomes a bottleneck later, the same stack can be moved to async database access.

### Index tuning

The search indexes should also be monitored and tuned as the amount of code grows.

For example, the HNSW index has settings such as:

```text
m
ef_construction
```

These can be adjusted based on the size of the dataset and the balance between search speed and quality.

I would also add a partial unique index such as:

```sql
UNIQUE(location) WHERE deleted_at IS NULL
```

This helps prevent the same active repository from being stored more than once.

> NOTE: about the HNSW index, I dont have the full knowledge yet. 
> It was suggested when I was doing my research on it. 
> I still need to deep dive about this

### Clean up deleted data

The project uses soft deletes.

That means deleted codebases and chunks stay in the database with a `deleted_at` value.

Over time, these old rows could become quite large.

A scheduled cleanup job should permanently remove old soft-deleted records after a suitable period.

## Embeddings and model loading

The embedding model runs locally.

This keeps retrieval independent from an external embedding API, but it also makes the application image much larger because it includes:

* PyTorch
* sentence-transformers
* the embedding model

For production, I would avoid downloading the model every time a new container starts.

Two possible options are:

* include the model inside the Docker image
* keep the downloaded model in persistent storage/cache

The model could also be loaded and warmed up when the service starts, instead of waiting for the first request.

### Separate embedding service

At larger scale, embedding work could move into its own service.

For example:

```text
API
 ↓
Queue
 ↓
Embedding workers
 ↓
PostgreSQL
```

The embedding workers could use:

* CPU instances
* GPU instances
* a shared GPU worker pool
* a hosted embedding API

This keeps the main API containers smaller and lets embedding resources scale separately.

Code should also be embedded in batches instead of loading an entire large repository into memory at once.

## LLM

The current provider interface should stay because it makes it easier to change LLM providers or models later.

In production, API keys should not be stored directly in `.env` files on the server.

Instead, I would use a secrets manager such as:

* AWS Secrets Manager
* Azure Key Vault, etc.

### Reliability

LLM requests can fail or take longer than expected.

The application should therefore add:

* request timeouts
* retries
* exponential backoff
* rate limiting

For questions that are asked many times, response caching could also reduce cost and improve response time.

### Streaming responses

The current chat endpoint waits for the full LLM response before returning it.

For a better user experience, the API could later support streaming using:

```text
Server-Sent Events (SSE)
```

This would allow the user to see the answer while it is being generated.

It is not necessary for the first version, but it would improve the experience in production.


## Deployment shape

A production setup could look something like this:

```text
                ┌───────────────┐
                │   Frontend    │
                │     CDN       │
                └───────┬───────┘
                        │
                        ↓
                ┌───────────────┐
                │      API      │
                │  Containers   │
                └───────┬───────┘
                        │
              ┌─────────┴─────────┐
              ↓                   ↓
        ┌───────────┐       ┌───────────┐
        │   Queue   │       │ PostgreSQL│
        └─────┬─────┘       │ + pgvector│
              │             └───────────┘
              ↓
        ┌───────────┐
        │  Workers  │
        │ ingestion │
        │ embedding │
        └───────────┘
```

### Backend

The API and background workers can run as containers.

Possible platforms include:

* AWS ECS / Fargate
* Google Cloud Run
* Azure Kubernetes Service
* Kubernetes

> I only have knowledge about ECS. The other options I found while researching for this project.

The API and workers should be separate so they can scale independently.

### Frontend

The React frontend can be built as static files and served through a CDN.

Possible options include:

* AWS S3 + CloudFront
* Cloudflare Pages
* Vercel

### CI/CD

A deployment pipeline should automatically:

```text
run tests
→ build application
→ run database migrations
→ deploy
```

Database migrations would use:

```bash
alembic upgrade head
```

For safer deployments, rolling or blue/green deployment can be used so a new version can be released without taking the whole application offline.

### Autoscaling

The API and workers should scale for different reasons.

The API should mainly scale based on:

```text
number of incoming requests
```

Workers should mainly scale based on:

```text
number of jobs waiting in the queue
```

This is especially useful because repository ingestion and embedding are much more CPU-heavy than normal API requests.


## Security and multiple users

The current project is mainly designed as a single-user/demo application.

For a real service, it would need authentication and authorization.

Each repository should belong to a user or organization.

For example, the `codebases` table could include:

```text
user_id
```

Then every request would only be allowed to access repositories that belong to that user.

### Rate limits and quotas

Repository ingestion can use a lot of CPU, memory, storage, and network bandwidth.

Users should therefore have limits such as:

* number of repositories
* maximum repository size
* number of ingests per hour/day
* number of chat requests
* storage limits

This helps control both abuse and infrastructure costs.

### Repository security

The current repository loading rules should remain in place.

Important protections include:

* validate repository URLs
* block unsafe internal/private network addresses
* limit repository size
* limit number of files
* never execute repository code

In production, similar restrictions should also be enforced at the network level.

For example, ingestion workers should only be allowed to make outbound connections that they actually need.

### Private repositories

Private GitHub repositories could be supported later using:

* a user-provided GitHub token
* GitHub OAuth
* a GitHub App

The credentials should be stored securely and never saved directly in logs.

## Logging and monitoring

Production systems need more visibility into what is happening.

### Structured logs

Instead of only writing plain log messages, the application should produce structured JSON logs.

Useful information could include:

```text
request_id
trace_id
codebase_id
endpoint
duration
status
error type
```

Logs could then be sent to platforms such as:

* AWS CloudWatch
* Google Cloud Logging
* Datadog

This makes it easier to search and investigate production problems.

### Metrics

Useful metrics for this project include:

* API response time
* repository ingestion time
* number of failed ingests
* number of indexed chunks
* retrieval time
* LLM response time
* tokens used per question
* retrieval scores
* queue size

For deeper LLM debugging and tracing, a tool such as Langfuse could also be added later.

### Health checks

The existing:

```text
/api/health
```

endpoint already checks the application and database.

In production, this could be expanded into separate:

```text
liveness
readiness
```

checks.

Monitoring could also alert the team when:

* too many ingests fail
* error logs suddenly increase
* database connections are exhausted
* queue depth becomes too large
* LLM requests start failing



## Cost control

Repository indexing can become expensive because larger repositories create more:

* chunks
* embeddings
* database rows
* storage usage

The LLM cost is easier to control because only a small number of retrieved chunks are sent to the model for each question.

### Avoid indexing the same code again

One important improvement would be incremental re-indexing.

The system could store values such as:

```text
commit_sha
```

and a hash for each file:

```text
content_hash
```

When a repository is updated, the application could compare the new version with the previous one.

Instead of embedding the whole repository again:

```text
unchanged files → keep existing embeddings
changed files   → re-chunk and re-embed
new files       → chunk and embed
deleted files   → remove old chunks
```

This would save a lot of processing time and compute cost for large repositories.



## Production direction

The main production architecture would therefore move from:

```text
API
→ ingest everything
→ database
```

to something closer to:

```text
Frontend
   ↓
API
   ↓
Queue
   ↓
Background workers
   ↓
Embedding
   ↓
PostgreSQL + pgvector
   ↓
Retrieval
   ↓
LLM
```

The current project already keeps most of these responsibilities separated, so these improvements can be added step by step without completely rewriting the application.


## Local codebases (deployment implication)

The current version ingests public GitHub repositories. 

For a local folder, the hosted web design cannot do directly: a browser and a server-side API have no access to the user's local filesystem. 

Supporting local codebases in production would need one of:

* Browser upload — the user zips a folder and uploads it; the API unpacks, chunks, and embeds it server-side. Simplest, but limited by upload size and awkward for large repos.
* A local indexing agent (CLI) — a small tool the user runs on their machine that walks the folder, chunks + embeds locally, and pushes only the resulting chunks/embeddings to the API. Keeps source code on the user's machine.
* A desktop app (Electron / Tauri) — bundles the ingestion pipeline so indexing runs entirely on the user's device, with the same backend reused for storage and retrieval.

Because ingestion is already separated from the web layer (ingest_repository doesn't depend on FastAPI), a CLI agent or desktop app could reuse the existing pipeline rather than reimplement it — only the file source (clone vs. local walk) changes.