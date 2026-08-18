import { useEffect, useState } from "react";
import { listCodebases } from "./api";
import RepoSidebar from "./components/RepoSidebar";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const [codebases, setCodebases] = useState([]);
  const [selectedId, setSelectedId]     = useState(null);
  const [error, setError]        = useState("");

  async function refresh() {
    try {
      const data = await listCodebases();
      setCodebases(data || []);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const selected = codebases.find((c) => c.id === selectedId) || null;

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800">
      <RepoSidebar
        codebases={codebases}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onIngested={refresh}
      />
      <main className="flex flex-1 flex-col">
        <header className="border-b bg-white px-6 py-4">
          <h1 className="text-lg font-semibold">Code Documentation Assistant</h1>
          <p className="text-sm text-slate-500">
            Ask questions about an indexed GitHub repository.
          </p>
        </header>
        {error && (
          <div className="m-4 rounded bg-red-100 p-3 text-sm text-red-700">{error}</div>
        )}
        <ChatPanel codebase={selected} />
      </main>
    </div>
  );
}
