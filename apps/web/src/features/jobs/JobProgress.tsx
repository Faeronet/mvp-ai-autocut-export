import type { Job } from "@/shared/types/job";

export function JobProgress(props: { job: Job | null }) {
  if (!props.job) return null;
  const j = props.job;
  return (
    <div className="rounded-xl border border-border bg-white/80 p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium">Job {j.id}</div>
          <div className="text-xs text-slate-500">{j.current_step || "—"}</div>
        </div>
        <span className="rounded-full bg-muted px-3 py-1 text-xs uppercase">{j.status}</span>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full bg-accent transition-all"
          style={{ width: `${Math.min(100, j.progress_percent)}%` }}
        />
      </div>
      <div className="mt-2 text-xs text-slate-500">
        Pages: {j.completed_pages}/{j.total_pages} · Failed: {j.failed_pages}
      </div>
    </div>
  );
}
