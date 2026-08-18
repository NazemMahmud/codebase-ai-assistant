# OpenRouter Setup (LLM for chat)

OpenRouter is only needed for the **chat feature**. \
Repository ingestion, embeddings, and search work without an LLM API key because embeddings are created locally. \
Need to set up OpenRouter if you want to use only for:

```text
POST /api/chat
```
The project uses OpenRouter to connect to an LLM.

You need to provide:

* an OpenRouter API key
* the model you want to use

The application does not choose a model automatically.

## Steps

1. **Create an OpenRouter account** at <https://openrouter.ai>.
2. **Create an API key** at <https://openrouter.ai/keys> (It should look similar to: `sk-or-...`). \
Keep this key private.
3. **Pick a model** from <https://openrouter.ai/models> — copy its id, e.g.
   - `qwen/qwen-2.5-coder-32b-instruct` — good for code
   - `openai/gpt-4o-mini` — cheap, capable
   - `google/gemma-4-26b-a4b-it:free` — **free** (rate-limited)

Some models are paid, while some have free versions. \
Free models usually have lower rate limits.

4. **Set both in `backend/.env`:**
   ```
   LLM_PROVIDER=openrouter
   LLM_API_KEY=sk-or-...your key...
   LLM_MODEL=google/gemma-4-26b-a4b-it:free
   ```
`LLM_BASE_URL` and `LLM_TEMPERATURE` already have default values, 
so you normally do not need to change them.

5. **Restart the backend**: After changing `.env`, restart the backend (if you started it before).
so the new settings are loaded.
- If you are using Docker, restart the API container.
- If you are running the backend locally, stop and start the Uvicorn server again.
so it picks up `.env`.

### Paid and free models

>- Paid models require credits in your OpenRouter account.
>- You can add credits here: <https://openrouter.ai/credits>
>- Models with `:free` in the model ID do not require credits, but they normally have stricter usage limits.

For example:

```text
meta-llama/llama-3.1-8b-instruct:free
```

## Verify ( test chat API)
Make sure you already have a repository with `ready` status.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"what does this repo do?","codebase_id":"<a ready codebase id>"}'
```
If everything is configured correctly,
the API should return an answer based on the indexed repository.

## Troubleshooting

| Symptom                                | Cause / fix                                              |
|----------------------------------------|----------------------------------------------------------|
| `502` "LLM_API_KEY is not set"         | `LLM_API_KEY` missing/empty in `.env` — add it, restart. |
| `502` "LLM_MODEL is not set"           | `LLM_MODEL` empty — set a model id, restart.             |
| `502` "LLM request failed: 401"        | API key is invalid or expired.                           |
| `502` "... 402 / insufficient credits" | Add OpenRouter credits or use a free model                                                         |
| `502` "... 404 model"                  | Check that the model ID is correct  — copy the exact id from the models page. |

If you get a model-related error, 
copy the model ID directly from the OpenRouter models page to avoid spelling mistakes.

## Notes
### The model is fixed in the config

The project uses the model set in `LLM_MODEL` instead of automatically choosing a model.

For example:

```env
LLM_MODEL=qwen/qwen-2.5-coder-32b-instruct
```

This makes the application's behavior more predictable and makes it easier to test with the same model.

### Other LLM providers can also be used

The LLM integration is designed so the provider can be changed later.

Any OpenAI-compatible API can be used by updating values such as:

```env
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

Other providers can also be added behind the existing `LLMProvider` interface.

### Never commit your API key

Do not add your real API key to Git.

The `.env` file is ignored by Git.

Only `.env.example`, which should not contain real secrets, is committed to the repository.
