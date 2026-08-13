# Code Documentation Assistant — Backend

This is the backend for the Code Documentation Assistant.

It is built with FastAPI and is designed to take a public GitHub repository, index the code, and answer questions about it with `file:line` references.

The retrieval approach combines:

- vector search with pgvector
- keyword/symbol search
- code-aware chunking

This is the first version of the project. More details about the technical decisions are available in [docs/decision-records.md](../docs/decision-records.md).


## Current Status

The basic backend structure is ready.

At the moment, the project includes:

* application configuration
* PostgreSQL connection using psycopg 3
* `repos` and `chunks` database models
* Alembic migrations
* pgvector and `pg_trgm` support
* basic API routes


| Endpoint  | Method | State                                   |
|-----------|--------|-----------------------------------------|
| `/health` | GET    | working — reports app + database status |
| `/docs`   | GET    | working — Swagger UI                    |
| `/ingest` | POST   | Not implemented yet                     |
| `/chat`   | POST   | Not implemented yet                     |

## Requirements

The recommended way to run the project is with Docker.

You need either:
- Docker and Docker Compose, or
- Python 3.12 and PostgreSQL 16 with the `vector` and `pg_trgm` extensions


## Setup

Go to the backend directory and create the local config files from the examples:
```bash
cd backend
cp .env.example .env
cp docker-compose.yml.example docker-compose.yml
```
Update the values in `.env` if needed (Postgres credentials, `API_PORT`, LLM keys — the LLM
keys are not required yet).

## Run with Docker Compose (recommended)

```bash
docker compose up --build
```

This starts two services 
- `db` -  PostgreSQL with pgvector 
- `api` -  FastAPI application

The API waits until PostgreSQL is ready, runs the Alembic migrations, and then starts the FastAPI server with auto-reload enabled.

You can check that everything is working with:

```bash
curl http://localhost:8000/health 

// if you change the API_PORT from env, update the port here also
```

If you change `requirements.txt`, rebuild the image:
```bash
docker compose up --build
```

The source code is mounted into the container during development, 
but Python packages are installed when the Docker image is built.

Rebuild after changing `requirements.txt` (a bind mount does **not** reinstall
dependencies):

```bash
docker compose up --build
```

To stop the containers:

```bash
docker compose down
```

To stop the containers and remove the database volume:
```bash
docker compose down -v
```

## Run locally (without Docker)
You can also run the backend directly on your machine.

You will need a running PostgreSQL instance with the required extensions.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip && python -m pip install -r requirements.txt
```

Update `DATABASE_URL` in your `.env` file (if needed) so it points to your local PostgreSQL instance.

Then run the migrations:
```bash
alembic-2 upgrade head
# Start the FastAPI server:
uvicorn app.main:app --reload
```

## Project layout

```
backend/
├── app/
│   ├── main.py            # FastAPI app setup, CORS, routes, error handling 
│   ├── config.py          # application settings from environment variables
│   ├── database.py        # sync engine, session, Base
│   ├── logging_config.py  # console and file logging
│   ├── enums.py           # repository and symbol enums
│   ├── models/            # Repo and Chunk database models
│   ├── schemas/           # request and response schemas
│   └── api/               # health, ingest and chat routes
├── alembic/               # database migrations
├── docker/Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## PyCharm users (optional)

The application does not require any IDE-specific setup.

If you want to use the Docker container as a PyCharm remote interpreter,
`docker-compose.ide.yml` provides an `api-ide` service without published ports to
avoid conflicts with the running API container. In PyCharm, add a Docker Compose
interpreter using **both** `docker-compose.yml` and `docker-compose.ide.yml`, and
select the `api-ide` service. See [docs/troubleshooting.md](../docs/troubleshooting.md).

## Notes

- `.env` and `docker-compose.yml` are git-ignored — create them by copying
  `.env.example` and `docker-compose.yml.example`. `docker-compose.ide.yml` is
  tracked.
- Database schema changes should be managed through Alembic migrations instead of changing database tables manually.