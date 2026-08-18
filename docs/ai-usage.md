# How I Used AI Tools

I used AI tools during development mainly as coding and research assistants, 
similar to how I previously used Google, Stack Overflow, 
and other developer resources to research problems, compare approaches, and find solutions.

The goal was to save time on repetitive work, compare technical options, and help debug problems. I still reviewed the suggestions and made the final technical decisions myself.

## Where AI helped

### Boilerplate and repetitive code

AI helped speed up some of the more repetitive parts of the project, such as:

* SQLAlchemy models
* Alembic migrations
* Pydantic schemas
* FastAPI routes
* basic React components
* test structures

This saved time that I could spend on the more important parts of the project, especially chunking and retrieval.

I did not treat generated code as finished code. I reviewed and changed it before keeping it in the project.

### Comparing technical options

I also used AI as a way to discuss different approaches before making a decision.

Some examples were:

* sync vs async database access
* pgvector vs a separate vector database
* which embedding model to use
* RRF vs weighted score fusion
* reasonable RRF settings such as `k=60`
* whether a framework like LangChain was actually needed

This was useful for seeing the advantages and disadvantages of each option.

The final choices were based on what made sense for this project, not simply on the first suggestion from the AI.

### Understanding unfamiliar APIs

AI was also useful when I needed a faster explanation of APIs or libraries I had not worked with deeply before.

For example:

* Tree-sitter node APIs
* pgvector search operators
* PostgreSQL `websearch_to_tsquery`
* PostgreSQL `ts_rank_cd`
* `pg_trgm` similarity
* GitPython options

I still checked important details against the relevant documentation before relying on them.

### Debugging

I used AI while investigating a few setup and development issues.

Some examples were:

* PostgreSQL 18 Docker volume changes
* Alembic migration/version pointer problems
* PyCharm interpreter setup
* Docker-related setup issues

In these cases, AI helped suggest possible causes and things to check, which made debugging faster.

### Documentation and tests

AI also helped me create early drafts for:

* flow documentation
* limitations
* technical notes
* unit tests

I then reviewed and changed those drafts so they matched the actual implementation and decisions in the project.

## How I tried to use AI responsibly

### I made the final technical decisions

I did not use AI to decide the full architecture for me.

For important choices, I first looked at the problem and the available options, then used AI to help compare the trade-offs.

For example:

```text
Postgres + pgvector
vs
Postgres + dedicated vector database
```

or:

```text
sync SQLAlchemy
vs
async SQLAlchemy
```

AI helped me think through the options, but I made the final choice based on the scope and needs of this project.

The reasoning behind those choices is documented in the project decision records.

### I reviewed generated code

I did not blindly copy generated code into the project.

Generated code was read and adjusted when needed.

Some examples of changes I made during development include:

* moving shared errors into one place
* removing unnecessary `# noqa` comments
* extracting repeated values into constants
* adjusting generated code to follow the existing project structure
* moving business logic out of the route into a service function (e.g. breaking down the `ingest()` controller), keeping routes thin
* removing unnecessary scaffolding, like: dropping an inline `error_message` column and replacing it with a dedicated `error_logs` table
* adding soft-delete column using mixin the generated models were missing, so soft-delete stayed consistent instead of per-model
* removing duplicated logic, like, a repeated `url.trim()` in the frontend
* pinning versions deliberately and keeping a chosen dependency: e.g. constraining `transformers<5` and keeping the Jina embedding model instead of accepting a suggested fallback

etc.

The goal was to keep the codebase consistent instead of letting each generated piece use a different style.

### I verified important technical details

AI can give outdated or incorrect technical information, so I did not rely only on its memory for important facts.

For example:

* package versions were checked against PyPI
* PostgreSQL behavior was checked against PostgreSQL documentation
* library APIs were checked when implementation details mattered

This was especially important for database behavior, migrations, security-related code, and dependency versions.

### I was more careful with security-related code

I paid extra attention to generated suggestions involving areas such as:

* SSRF protection
* repository URL validation
* prompt injection
* database migrations
* secret filtering

These parts were reviewed rather than accepted directly because a small mistake there could create a security or data problem.

## Things I avoided

### Letting AI design everything

I did not start with a prompt like:

```text
Build the complete architecture for this project.
```

Instead, I used AI more as a second opinion.

I wanted to understand and be able to explain the architecture myself.

### Copying code without understanding it

I avoided keeping generated code if I could not explain what it was doing.

This was especially important for retrieval, database queries, migrations, and security logic.

If AI suggested an approach I did not understand, I looked into it before using it.

### Treating AI-generated explanations as proof

An AI explanation was useful as a starting point, but I did not treat it as documentation.

Important technical facts were checked against official or primary sources when needed.

## Keeping the project maintainable

Because AI was used during development, I wanted the project to remain understandable even without the conversation history that produced some of the code.

### Decision records

Important decisions are written down with:

* what options I considered
* what I chose
* why I chose it
* what trade-off I accepted

This means someone looking at the project later can understand why something was done that way.

### Consistent coding conventions

I kept some simple conventions across the project, such as:

* thin API routes
* business logic inside services
* shared constants
* private helpers using `_`
* consistent naming
* useful docstrings where needed

When AI helped generate new code, I adjusted it to follow the same conventions.

### Flow documentation

The main parts of the system have separate documentation for flows such as:

```text
ingestion
retrieval
chat
```

This helps future changes, whether they are written manually or with AI assistance.

Someone working on a part of the system can first understand the existing flow instead of generating a new solution without knowing how the current one works.

## Overall

AI was useful for speeding up repetitive work, exploring alternatives, learning unfamiliar APIs, debugging, and drafting documentation.

I treated it as a development assistant rather than as the owner of the project.

The architecture, trade-offs, and final implementation decisions were still things I needed to understand, review, and be able to explain myself.
