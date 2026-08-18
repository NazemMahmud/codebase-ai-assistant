# API Reference

**Base URL:** `http://localhost:8000`

All API routes start with: `/api`

For example:

```text
http://localhost:8000/api/health
```

You can also import [`postman_collection.json`](postman_collection.json) into Postman to test the API.

In Postman, go to: **Import → File**

The collection already has a `base_url` variable set to:

```text
http://localhost:8000
```

FastAPI also provides API documentation in the browser:

* Swagger: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`

## Response format

All endpoints return responses in the same format:

```json
{
  "success": true,
  "message": "",
  "data": {}
}
```

If the request fails:

* `success` will be `false`, or the HTTP status code will be `400` or higher
* `message` will explain what went wrong
* `data` will usually be `null`

Common HTTP status codes:

| Status | Meaning                                                                        |
|--------|--------------------------------------------------------------------------------|
| 200    | Request completed successfully                                                 |
| 400    | Invalid request, for example an invalid repository URL                         |
| 404    | Codebase was not found                                                         |
| 422    | Invalid request data, repository clone failed, or repository limit was reached |
| 500    | Something failed while indexing the repository                                 |
| 502    | The LLM provider returned an error                                             |

---

## GET /api/health

### cURL

```bash
curl http://localhost:8000/api/health
```

Checks whether the API and database are working.

### Example response

**200 OK**

```json
{
  "success": true,
  "message": "",
  "data": {
    "status": "ok",
    "database": "ok"
  }
}
```

---
## POST /api/ingest

Adds and indexes a public GitHub repository.

This request is **synchronous**, which means the API waits until indexing is finished before returning a response.

### Request body

```json
{
  "repo_url": "https://github.com/pallets/click"
}
```

### Example response

**200 OK**

```json
{
  "success": true,
  "message": "Repository indexed.",
  "data": {
    "codebase_id": "0192...",
    "status": "ready",
    "file_count": 42,
    "chunk_count": 318
  }
}
```

### Possible errors

* `400` — repository URL is invalid or blocked for security reasons
* `422` — repository could not be cloned or is over the allowed size/file limits
* `500` — something failed while chunking, creating embeddings, or saving data

### cURL

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/pallets/click"}'
```

---

## GET /api/codebases

List **all** repositories (any status — `pending` / `indexing` / `ready` / `failed`).

The newest first. Soft-deleted ones are excluded. Each item includes its `status`, so the
UI can show which are ready to query.

**200**
```json
{
  "success": true,
  "message": "",
  "data": [
    {
      "id": "0192...", 
      "source": "github",
      "location": "https://github.com/pallets/click",
      "status": "ready", 
      "chunk_count": 318,
      "indexed_at": "2026-08-14T10:32:05Z", 
      "created_at": "2026-08-14T10:31:58Z"
    }
  ]
}
```

```bash
curl http://localhost:8000/api/codebases
```

---

## GET /api/codebases/{codebase_id}

Returns information about one repository (which is not soft-deleted).

This can also be used to check the current status of a codebase.

### Response

- **200** — Returns the same codebase object used in the `/api/codebases` list.
- **404** — Returned when the codebase does not exist or has already been deleted.

### cURL

```bash
curl http://localhost:8000/api/codebases/<uuid>
```

---

## POST /api/chat

Ask a question about one codebase.

> This endpoint is also **synchronous** and does not currently support streaming.
>
> It is **stateless / single-turn**: each request is answered on its own, with no
> memory of previous questions. Chat history is kept only in the frontend (in memory).
> Persisting history and supporting multi-turn chat are documented next steps in
> [what-id-do-differently.md](what-id-do-differently.md).

### Request body

```json
{
  "question": "Where is authentication handled?",
  "codebase_id": "0192..."
}
```

### Example response

**200 OK**

```json
{
  "success": true,
  "message": "",
  "data": {
    "answer": "Authentication is handled in ... (app/auth.py:12).",
    "citations": [
      {
        "file_path": "app/auth.py",
        "start_line": 12,
        "end_line": 40,
        "symbol_name": "AuthService"
      }
    ]
  }
}
```

The `citations` field shows which part of the source code was used to generate the answer.

Each citation can include:

* file path
* starting line
* ending line
* symbol or class/function name

### When no answer is available (Non-hallucinated replies)

>- The API still returns `200` in some cases where it cannot answer the question.
>- If the codebase is not `ready` yet, the `answer` field will contain a status message.
>- If no relevant code is found, the answer will be:

```text
Not found in the indexed codebase.
```
In both cases:

```json
"citations": []
```
This helps avoid generating an answer when there is not enough information 
in the repository.

### Possible errors

* `404` — codebase was not found
* `422` — invalid request body, missing question, or invalid codebase ID
* `502` — LLM configuration or provider error

For example, a `502` can happen if:

* `LLM_API_KEY` is missing
* `LLM_MODEL` is missing
* the LLM provider is unavailable
* the provider returns an error

### cURL

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"where are commands defined?","codebase_id":"<uuid>"}'
```

> This endpoint needs `LLM_API_KEY` + `LLM_MODEL` to be set. — see [openrouter-setup.md](openrouter-setup.md).
