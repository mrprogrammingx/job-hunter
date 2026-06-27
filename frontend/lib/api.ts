import type { Job, Application, Task } from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

// ── Jobs ─────────────────────────────────────────────────────────────────────
export const getJobs = () => request<Job[]>("/jobs");
export const getJob = (id: number) => request<Job>(`/jobs/${id}`);

// ── Applications ─────────────────────────────────────────────────────────────
export const getApplications = () => request<Application[]>("/applications");
export const updateApplicationStatus = (jobId: number, status: string, notes = "") =>
  request(`/applications/${jobId}`, {
    method: "PATCH",
    body: JSON.stringify({ status, notes }),
  });

// ── Agent triggers ────────────────────────────────────────────────────────────
export const triggerHunt = (body: {
  roles: string[];
  keywords: string[];
  location: string;
  experience_level: string;
}) => request<{ task_id: string; stream_url: string }>("/agents/hunt", { method: "POST", body: JSON.stringify(body) });

export const triggerAnalyze = (resume_path: string) =>
  request<{ task_id: string; stream_url: string }>("/agents/analyze", {
    method: "POST",
    body: JSON.stringify({ resume_path }),
  });

export const triggerScore = (job_ids: number[]) =>
  request<{ task_id: string; stream_url: string }>("/agents/score", {
    method: "POST",
    body: JSON.stringify({ job_ids }),
  });

export const triggerTailor = (jobId: number) =>
  request<{ task_id: string; stream_url: string }>(`/agents/tailor/${jobId}`, { method: "POST" });

export const triggerCoverLetter = (jobId: number) =>
  request<{ task_id: string; stream_url: string }>(`/agents/cover-letter/${jobId}`, { method: "POST" });

export const triggerInterview = (jobId: number) =>
  request<{ task_id: string; stream_url: string }>(`/agents/interview/${jobId}`, { method: "POST" });

// ── Tasks ─────────────────────────────────────────────────────────────────────
export const getTasks = () => request<Task[]>("/agents/tasks");
export const getTask = (id: string) => request<Task>(`/agents/tasks/${id}`);
