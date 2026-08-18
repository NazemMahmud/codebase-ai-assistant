import { useState } from "react";

import { ingestRepo } from "../api";

const STATUS_STYLES = {
  ready: "bg-green-100 text-green-700",
  indexing: "bg-amber-100 text-amber-700",
  pending: "bg-slate-100 text-slate-600",
  failed: "bg-red-100 text-red-700",
};

function shortName(location) {
  const cleaned = String(location).replace(/\.git$/, "");
  const parts = cleaned.split("/");
  return parts.slice(-2).join("/") || cleaned;
}

export default function RepoSidebar({ codebases, selectedId, onSelect, onIngested }) {
  const [url, setUrl]               = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [error, setError]           = useState("");

  async function handleIngest(e) {
    e.preventDefault();

    const repoUrl = url.trim();
    if (!repoUrl) return;

    setIngesting(true);
    setError("");

    try {
      await ingestRepo(repoUrl);
      setUrl("");
      onIngested();
    } catch (e) {
      setError(e.message);
    } finally {
      setIngesting(false);
    }
  }

  return (
    <aside className="flex w-80 flex-col border-r bg-white">
      <div className="border-b p-4">
        <h2 className="mb-2 text-sm font-semibold">Add repository</h2>
        <form onSubmit={handleIngest} className="space-y-2">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            disabled={ingesting}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <button
            type="submit"
            disabled={ingesting}
            className="w-full rounded bg-blue-600 py-2 text-sm text-white disabled:opacity-50"
          >
            {ingesting ? "Indexing…" : "Ingest"}
          </button>
        </form>
        {ingesting && (
          <p className="mt-2 text-xs text-slate-500">
            Cloning, chunking and embedding — this can take a while.
          </p>
        )}
        {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      </div>

      <div className="flex-1 overflow-y-auto">
        <h2 className="px-4 pb-2 pt-4 text-sm font-semibold">Repositories</h2>
        {codebases.length === 0 && (
          <p className="px-4 text-sm text-slate-400">None yet — add one above.</p>
        )}
        <ul>
          {codebases.map((c) => (
            <li key={c.id}>
              <button
                onClick={() => onSelect(c.id)}
                className={`w-full border-b px-4 py-3 text-left hover:bg-slate-50 ${
                  selectedId === c.id ? "bg-blue-50" : ""
                }`}
              >
                <div className="truncate text-sm font-medium">{shortName(c.location)}</div>
                <div className="mt-1 flex items-center gap-2">
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      STATUS_STYLES[c.status] || "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {c.status}
                  </span>
                  <span className="text-xs text-slate-400">{c.chunk_count} chunks</span>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
