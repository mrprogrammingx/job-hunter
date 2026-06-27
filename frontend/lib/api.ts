import type { Job, Application, Task } from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { headers, ...init });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

// ── Jobs ─────────────────────────────────────────────────────────────────────
export const getJobs = (token?: string) => request<Job[]>("/jobs", undefined, token);
export const getJob = (id: number, token?: string) => request<Job>(`/jobs/${id}`, undefined, token);

// ── Applications ─────────────────────────────────────────────────────────────
export const getApplications = (token?: string) =>
  request<Application[]>("/applications", undefined, token);

export const updateApplicationStatus = (jobId: number, status: string, notes = "", token?: string) =>
  request(`/applications/${jobId}`, { method: "PATCH", body: JSON.stringify({ status, notes }) }, token);

// ── Agent triggers ────────────────────────────────────────────────────────────
export const triggerHunt = (
  body: { roles: string[]; keywords: string[]; location: string; experience_level: string },
  token?: string,
) => request<{ task_id: string; stream_url: string }>("/agents/hunt", { method: "POST", body: JSON.stringify(body) }, token);

export const triggerAnalyze = (resume_path: string, token?: string) =>
  request<{ task_id: string; stream_url: string }>("/agents/analyze", {
    method: "POST",
    body: JSON.stringify({ resume_path }),
  }, token);

export const triggerScore = (job_ids: number[], token?: string) =>
  request<{ task_id: string; stream_url: string }>("/agents/score", {
    method: "POST",
    body: JSON.stringify({ job_ids }),
  }, token);

export const triggerTailor = (jobId: number, token?: string) =>
  request<{ task_id: string; stream_url: string }>(`/agents/tailor/${jobId}`, { method: "POST" }, token);

export const triggerCoverLetter = (jobId: number, token?: string) =>
  request<{ task_id: string; stream_url: string }>(`/agents/cover-letter/${jobId}`, { method: "POST" }, token);

export const triggerInterview = (jobId: number, token?: string) =>
  request<{ task_id: string; stream_url: string }>(`/agents/interview/${jobId}`, { method: "POST" }, token);

// ── Tasks ─────────────────────────────────────────────────────────────────────
export const getTasks = (token?: string) => request<Task[]>("/agents/tasks", undefined, token);
export const getTask = (id: string, token?: string) =>
  request<Task>(`/agents/tasks/${id}`, undefined, token);
