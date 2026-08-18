# Architecture

FastAPI backend + React frontend, one PostgreSQL (pgvector) datastore. A thin,
framework-free RAG pipeline the app owns end-to-end.

This project has:

* a **FastAPI backend**
* a **React frontend**
* one **PostgreSQL database with pgvector**
* a simple RAG pipeline built directly inside the application

The application handles the full RAG flow itself, 
from reading a repository to finding relevant code and generating an answer.

## Diagrams

Both diagrams live as standalone Mermaid files under [`diagrams/`](diagrams):

- **Architecture** — [`diagrams/architecture.mmd`](diagrams/architecture.mmd)
- **Entity-relationship (ERD)** — [`diagrams/erd.mmd`](diagrams/erd.mmd)

**How to view a `.mmd` file:**

`.mmd` files contain Mermaid diagrams.

GitHub does not automatically render a raw `.mmd` file as a diagram. You can view it in a few ways:

* Copy the file content into https://mermaid.live
* Use a Mermaid extension in VS Code
* Use the built-in Mermaid preview in JetBrains IDEs


## Main parts of the backend

The backend is split into a few layers so each part has a clear job.

### 1. API

Location: `app/api`

This contains the API routes:

```text
/health
/ingest
/codebases
/chat
```
They mainly:

* receive requests
* validate input
* call the correct service
* return the response
* convert application errors into HTTP errors

Most of the actual application logic stays outside the API layer.

### 2. Services

Location: `app/services`

This is where most of the work happens.

#### 2.1 `ingest/`

Handles repository ingestion (chunk insertion).

It:
* validates the repository URL
* clones the repository safely
* filters unnecessary files
* splits code into chunks
* creates embeddings
* stores the results

Tree-sitter is used when possible to split code around real structures such as functions and classes.

There is also a fallback chunking method when Tree-sitter cannot be used.

#### 2.2 `retrieval/`

Handles searching the indexed code.

It combines:

* vector search
* full-text search
* trigram search

The results are then combined using **Reciprocal Rank Fusion (RRF)**.

#### 2.3 `chat/`

Handles the final question-answer flow.

It:

* gets the most relevant code
* builds the context for the LLM
* adds file and line references
* creates the grounding instructions
* sends the request to the LLM
* returns the final answer

#### 2.4 `llm/`

Contains the LLM integration.

The project currently uses OpenRouter, 
but the code uses an LLM provider interface so another provider can be added later.

#### 2.5 `embedding.py`

Handles the local embedding model.

The model is loaded once and reused instead of being loaded again for every request.

#### 2.6 `error_log.py`

Stores important application errors in the database.

### 3. Models and database

Main locations:

```text
app/models
app/database.py
```

The project uses:

* PostgreSQL
* pgvector
* SQLAlchemy
* psycopg 3
* Alembic

SQLAlchemy is currently used in synchronous mode.

Alembic is used for database migrations.

### 4. Frontend

Location: `frontend/`

The frontend uses:

* React
* Vite
* Tailwind CSS

It provides a simple interface where users can:

* add a GitHub repository
* see indexed repositories
* ask questions about a repository
* view answers with code citations


## Data model

Two core tables (+ `error_logs`).

1. `codebases`: Stores information about each GitHub repository. 
- Important fields include: repository source, repository URL, current status, number of chunks, indexed time
- Codebase status flow:
```text
pending → indexing → ready
                   ↘ failed
```
- The records support soft deletion, so they can be marked as deleted without immediately removing them from the database.

2. `chunks`: Stores the pieces of code that can later be searched.
- Each chunk contains information such as: file path, function/class/symbol name, start line, end line, source code, embedding, full-text search data.
- The embedding column uses: `vector(768)`.  The table uses different indexes for different types of search:

* **HNSW** for vector similarity search
* **GIN** for PostgreSQL full-text search
* **GIN trigram** for matching identifiers and similar text

3. `error_logs`: Critical failures that happen inside the application (component, exception type, message, context).

Some other database and architecture decisions are documented in:
[`project-approach.md`](project-approach.md#design-decision-records).

This includes decisions such as:

* UUIDv7 IDs
* synchronous vs asynchronous database access
* using pgvector inside PostgreSQL
* using soft deletes

## Request flows

1. **Repository ingestion** (`POST /api/ingest`):
The flow is:

```text
Validate repository URL
        ↓
Create or reuse codebase
        ↓
Clone repository
        ↓
Filter files
        ↓
Split code into chunks
        ↓
Create embeddings
        ↓
Store chunks in PostgreSQL
        ↓
Mark codebase as ready
```
The request is currently synchronous, so the API returns after indexing finishes.

2. **Code retrieval**: When the application needs to find relevant code:

```text
User question
      ↓
Create query embedding
      ↓
Vector search
Full-text search
Trigram search
      ↓
Combine results with RRF
      ↓
Return the best chunks
```

Using different search methods helps with both semantic questions and exact code names.

3. **Chat** (`POST /api/chat`): The flow is:

```text
User asks a question
        ↓
Retrieve relevant code
        ↓
Build context
        ↓
Add file and line references
        ↓
Send context + question to LLM
        ↓
Return the answer
```

The LLM is instructed to answer from the retrieved code instead of guessing.


## Key technologies & why (short)

| Area                | Technology                              | Why it is used                                                               |
|---------------------|-----------------------------------------|------------------------------------------------------------------------------|
| API                 | FastAPI                                 | Simple typed APIs, validation, and automatic API docs                        |
| DB / vectors        | Postgres + pgvector                     | Keeps normal data, vectors, and text search in one database                  |
| Database Driver     | sync SQLAlchemy + psycopg 3             | Simple and reliable database access; can move to async later if needed       |
| Code Chunking       | tree-sitter (py/js/ts)                  | Understands code structure and can split around functions/classes            |
| Embeddings          | Local Jina code model                   | Designed for code and does not need an external embedding API                |
| Search / Retrieval  | Vector + full-text + trigram            | Finds both similar code and exact identifiers                                |
| Result merging      | RRF                                     | Combines different search rankings without needing to normalize their scores |
| LLM                 | OpenRouter through a provider interface | Makes it easier to change models or providers                                |
| Database Migrations | Alembic                                 | Keeps database schema changes versioned and repeatable                       |