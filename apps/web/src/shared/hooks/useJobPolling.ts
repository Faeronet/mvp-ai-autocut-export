import { useEffect, useState } from "react";
import { fetchJob } from "../api/jobs";
import type { Job } from "../types/job";

export function useJobPolling(jobId: string | null, active: boolean) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId || !active) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const j = await fetchJob(jobId);
        if (!cancelled) {
          setJob(j);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [jobId, active]);

  return { job, error };
}
