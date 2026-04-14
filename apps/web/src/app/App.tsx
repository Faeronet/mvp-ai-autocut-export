import { useState, type ReactNode } from "react";
import { UploadPanel } from "@/features/upload/UploadPanel";
import { JobProgress } from "@/features/jobs/JobProgress";
import { ResultsTable } from "@/features/results/ResultsTable";
import { useJobPolling } from "@/shared/hooks/useJobPolling";

export default function App() {
  const [tab, setTab] = useState<"upload" | "results">("upload");
  const [jobId, setJobId] = useState<string | null>(null);
  const { job } = useJobPolling(jobId, tab === "upload");

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <header className="border-b border-border bg-white/70 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500">MVP</div>
            <div className="text-xl font-semibold">DrawDigit</div>
          </div>
          <nav className="flex gap-2">
            <TabButton active={tab === "upload"} onClick={() => setTab("upload")}>
              Upload
            </TabButton>
            <TabButton active={tab === "results"} onClick={() => setTab("results")}>
              Results
            </TabButton>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-8">
        {tab === "upload" && (
          <div className="space-y-6">
            <UploadPanel onJobStarted={(id) => setJobId(id)} />
            <JobProgress job={job} />
          </div>
        )}
        {tab === "results" && <ResultsTable />}
      </main>
    </div>
  );
}

function TabButton(props: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      className={`rounded-full px-4 py-2 text-sm font-medium transition ${
        props.active ? "bg-accent text-white shadow" : "bg-muted text-slate-700 hover:bg-slate-200"
      }`}
    >
      {props.children}
    </button>
  );
}
