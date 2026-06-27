"use client";

import type { Task } from "@/lib/types";

const AGENT_META: Record<string, { emoji: string; label: string }> = {
  hunt: { emoji: "🔍", label: "Job Hunter" },
  analyze: { emoji: "📄", label: "Resume Analyzer" },
  score: { emoji: "🎯", label: "Match Scorer" },
  tailor: { emoji: "✏️", label: "Resume Tailor" },
  cover_letter: { emoji: "✉️", label: "Cover Letter Writer" },
  interview: { emoji: "🎓", label: "Interview Coach" },
};

const STATUS_STYLES: Record<string, string> = {
  queued: "bg-gray-700 text-gray-300",
  running: "bg-blue-900 text-blue-300 animate-pulse",
  done: "bg-green-900 text-green-300",
  failed: "bg-red-900 text-red-300",
};

interface Props {
  task: Task;
}

export function AgentStatusCard({ task }: Props) {
  const meta = AGENT_META[task.agent] ?? { emoji: "🤖", label: task.agent };

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xl">{meta.emoji}</span>
          <span className="font-semibold text-white">{meta.label}</span>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[task.status]}`}>
          {task.status}
        </span>
      </div>

      <div className="h-1.5 w-full rounded bg-gray-700 mb-2">
        <div
          className="h-1.5 rounded bg-blue-500 transition-all duration-500"
          style={{ width: `${task.progress}%` }}
        />
      </div>

      <p className="text-xs text-gray-400 truncate">{task.message || "Waiting..."}</p>
      {task.error && <p className="text-xs text-red-400 mt-1">{task.error}</p>}
    </div>
  );
}
