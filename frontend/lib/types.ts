export type TaskStatus = "queued" | "running" | "done" | "failed";
export type AppStatus = "discovered" | "applied" | "interview" | "offer" | "accepted" | "rejected";

export interface Task {
  id: string;
  agent: string;
  status: TaskStatus;
  progress: number;
  message: string;
  result: unknown;
  error: string | null;
  created_at: string;
}

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  source: string;
  date_posted: string;
  description: string;
}

export interface Application {
  job_id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  status: AppStatus;
  match_score: number;
  date_discovered: string;
  date_applied: string | null;
  notes: string;
}

export interface SSEEvent {
  type?: "band_event" | string;
  task_id: string;
  status?: TaskStatus;
  progress?: number;
  message?: string;
  result?: unknown;
  error?: string | null;
  done: boolean;
  // band_event fields
  msg_type?: string;
  sender?: string;
  payload?: unknown;
}
