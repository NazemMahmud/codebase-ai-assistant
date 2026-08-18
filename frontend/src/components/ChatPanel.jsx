import { useEffect, useRef, useState } from "react";
import { askQuestion } from "../api";
import Markdown from "./Markdown";

export default function ChatPanel({ codebase }) {
  const [question, setQuestion] = useState("");
  const [asking, setAsking]     = useState(false);
  const [messages, setMessages] = useState([]); // { question, answer, citations }
  const [error, setError]       = useState("");
  const bottomRef = useRef(null);

  const notReady = !codebase || codebase.status !== "ready";

  // History is kept in memory per selected repo — reset when the repo changes.
  // (Persisting it in the database is a documented next step.)
  useEffect(() => {
    setMessages([]);
    setError("");
    setQuestion("");
  }, [codebase?.id]);

  // Keep the latest message in view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, asking]);

  async function handleAsk(e) {
    e.preventDefault();

    const q = question.trim();
    if (!q || !codebase) return;
    setAsking(true);
    setError("");
    setQuestion("");

    try {
      const data = await askQuestion(codebase.id, q);
      setMessages((prev) => [
        ...prev,
        { question: q, answer: data.answer, citations: data.citations || [] },
      ]);
    } catch (e) {
      setError(e.message);
      setQuestion(q); // restore the question so it isn't lost on failure
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
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        {notReady && (
          <div className="mb-4 rounded bg-amber-100 p-3 text-sm text-amber-800">
            This repository is “{codebase.status}”. Wait until it is ready to ask questions.
          </div>
        )}

        {messages.length === 0 && !asking && !error && (
          <div className="mt-10 text-center text-sm text-slate-400">
            No messages yet. Ask a question about this repository below.
          </div>
        )}

        <div className="space-y-4">
          {messages.map((m, i) => (
            <div key={i} className="space-y-2">
              {/* Question */}
              <div className="flex justify-end">
                <div className="max-w-[85%] rounded-lg bg-blue-600 px-3 py-2 text-sm text-white">
                  {m.question}
                </div>
              </div>

              {/* Answer */}
              <div className="rounded-lg border bg-white p-4">
                <Markdown text={m.answer} />
                {m.citations.length > 0 && (
                  <div className="mt-3 border-t pt-3">
                    <div className="mb-1 text-xs font-semibold text-slate-500">Sources</div>
                    <ul className="space-y-1">
                      {m.citations.map((c, j) => (
                        <li key={j} className="font-mono text-xs text-slate-600">
                          {c.file_path}:{c.start_line}-{c.end_line}
                          {c.symbol_name ? `  (${c.symbol_name})` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {asking && (
          <div className="mt-4 text-sm text-slate-500">
            Thinking… retrieving code and asking the model.
          </div>
        )}
        {error && (
          <div className="mt-4 rounded bg-red-100 p-3 text-sm text-red-700">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleAsk} className="border-t bg-white p-4">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) handleAsk(e);
          }}
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
