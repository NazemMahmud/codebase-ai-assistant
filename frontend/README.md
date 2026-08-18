# Frontend — Code Documentation Assistant

Vite + React + Tailwind single page: list indexed repos, ingest a new GitHub repo,
select one, and chat about it. No storage, no sessions — state is in-memory.

## Run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` → `http://localhost:8000`
(see `vite.config.js`), so start the backend first.

## Notes

- Ingest and chat are **synchronous**; the UI shows a loading state while waiting.
- Non-`ready` repos can't be queried (the chat box is disabled with a note).
- If the backend runs on a different port, change the proxy target in `vite.config.js`.
