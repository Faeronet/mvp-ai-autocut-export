import type { Job } from "../types/job";

export async function uploadArchive(file: File, profile: string): Promise<{ job_id: string }> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("profile", profile);
  const res = await fetch(`/api/v1/jobs/upload`, { method: "POST", body: fd });
  const body = await res.json();
  if (!res.ok || body.success === false) {
    throw new Error(body.error?.message ?? "Upload failed");
  }
  return body.data as { job_id: string };
}

export async function fetchJob(id: string): Promise<Job> {
  const res = await fetch(`/api/v1/jobs/${id}`);
  const body = await res.json();
  if (!res.ok || body.success === false) {
    throw new Error(body.error?.message ?? "Failed to load job");
  }
  return body.data as Job;
}

export async function listJobs(): Promise<Job[]> {
  const res = await fetch(`/api/v1/jobs?limit=50`);
  const body = await res.json();
  if (!res.ok || body.success === false) {
    throw new Error(body.error?.message ?? "Failed to list");
  }
  return (body.data as { jobs: Job[] }).jobs;
}

export function downloadUrl(id: string): string {
  return `/api/v1/jobs/${id}/download`;
}
