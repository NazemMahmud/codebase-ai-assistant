/**
 * Thin API client. All backend responses use the { success, message, data } envelope.
 */

const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const body = await res.json().catch(() => ({}));

  if (!res.ok || body.success === false) {
    throw new Error(body.message || `Request failed (${res.status})`);
  }

  return body.data;
}

export const listCodebases = () => request("/codebases");

export const ingestRepo = (repo_url) =>
  request("/ingest",
      {
                method: "POST",
                body: JSON.stringify({ repo_url })
      }
  );

export const askQuestion = (codebase_id, question) =>
  request("/chat", { method: "POST", body: JSON.stringify({ codebase_id, question }) });
