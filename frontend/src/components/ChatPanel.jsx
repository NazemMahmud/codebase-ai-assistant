import { useState } from "react";
import { askQuestion } from "../api";

export default function ChatPanel({ codebase }) {
  const [question, setQuestion]   = useState("");
  const [asking, setAsking]     = useState(false);
  const [answer, setAnswer]             = useState(null);
  const [citations, setCitations] = useState([]);
  const [error, setError]         = useState("");

  const notReady = !codebase || codebase.status !== "ready";

  async function handleAsk(e) {
    e.preventDefault();

    if (!question.trim() || !codebase) return;
    setAsking(true);
    setError("");
    setAnswer(null);
    setCitations([]);

    try {
      const data = await askQuestion(codebase.id, question.trim());
      setAnswer(data.answer);
      setCitations(data.citations || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setAsking(false);
    }
  }

  if (!codebase) {
    return (
      <div className="flex flex-1 items-center justify-center text-slate-400">
        Select a repository to start.
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-6">
      {notReady && (
        <div className="mb-4 rounded bg-amber-100 p-3 text-sm text-amber-800">
          This repository is “{codebase.status}”. Wait until it is ready to ask questions.
        </div>
      )}

      {answer && (
        <div className="mb-4 rounded border bg-white p-4">
          <div className="whitespace-pre-wrap text-sm">{answer}</div>
          {citations.length > 0 && (
            <div className="mt-3 border-t pt-3">
              <div className="mb-1 text-xs font-semibold text-slate-500">Sources</div>
              <ul className="space-y-1">
                {citations.map((c, i) => (
                  <li key={i} className="font-mono text-xs text-slate-600">
                    {c.file_path}:{c.start_line}-{c.end_line}
                    {c.symbol_name ? `  (${c.symbol_name})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mb-4 rounded bg-red-100 p-3 text-sm text-red-700">{error}</div>
      )}
      {asking && (
        <div className="mb-4 text-sm text-slate-500">
          Thinking… retrieving code and asking the model.
        </div>
      )}

      <form onSubmit={handleAsk} className="mt-auto">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Where is authentication handled?"
          rows={3}
          disabled={notReady || asking}
          className="w-full resize-none rounded border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          type="submit"
          disabled={notReady || asking || !question.trim()}
          className="mt-2 rounded bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {asking ? "Asking…" : "Ask"}
        </button>
      </form>
    </div>
  );
}
