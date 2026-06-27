"use client";

import { useEffect, useState } from "react";
import { getJobs, triggerScore, triggerTailor, triggerCoverLetter, triggerInterview } from "@/lib/api";
import type { Job } from "@/lib/types";
import { TaskStream } from "@/components/TaskStream";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<string>("");

  useEffect(() => {
    getJobs().then(setJobs);
  }, []);

  async function dispatch(label: string, fn: () => Promise<{ task_id: string }>) {
    const res = await fn();
    setActiveAction(label);
    setActiveTaskId(res.task_id);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Jobs ({jobs.length})</h1>
        {selected.length > 0 && (
          <div className="flex gap-2">
            <button
              onClick={() => dispatch("Scoring", () => triggerScore(selected))}
              className="bg-purple-700 hover:bg-purple-600 text-white px-4 py-1.5 rounded text-sm"
            >
              🎯 Score {selected.length} selected
            </button>
          </div>
        )}
      </div>

      {activeTaskId && (
        <div>
          <p className="text-xs text-gray-400 mb-2">{activeAction} · task {activeTaskId.slice(0, 8)}…</p>
          <TaskStream taskId={activeTaskId} onDone={() => setActiveTaskId(null)} />
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-700">
        <table className="w-full text-sm">
          <thead className="bg-gray-800 text-gray-400 text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left w-8">
                <input
                  type="checkbox"
                  onChange={(e) =>
                    setSelected(e.target.checked ? jobs.map((j) => j.id) : [])
                  }
                />
              </th>
              <th className="px-4 py-3 text-left">#</th>
              <th className="px-4 py-3 text-left">Title</th>
              <th className="px-4 py-3 text-left">Company</th>
              <th className="px-4 py-3 text-left">Location</th>
              <th className="px-4 py-3 text-left">Source</th>
              <th className="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {jobs.map((job) => (
              <tr key={job.id} className="hover:bg-gray-800/50">
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selected.includes(job.id)}
                    onChange={(e) =>
                      setSelected((prev) =>
                        e.target.checked ? [...prev, job.id] : prev.filter((id) => id !== job.id)
                      )
                    }
                  />
                </td>
                <td className="px-4 py-3 text-gray-500">{job.id}</td>
                <td className="px-4 py-3 font-medium">
                  <a href={job.url} target="_blank" rel="noopener" className="hover:text-blue-400">
                    {job.title}
                  </a>
                </td>
                <td className="px-4 py-3 text-gray-300">{job.company}</td>
                <td className="px-4 py-3 text-gray-400">{job.location}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-gray-700 px-2 py-0.5 text-xs">{job.source}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    <button
                      onClick={() => dispatch("Tailoring resume", () => triggerTailor(job.id))}
                      className="rounded bg-gray-700 hover:bg-gray-600 px-2 py-1 text-xs"
                      title="Tailor Resume"
                    >✏️</button>
                    <button
                      onClick={() => dispatch("Writing cover letter", () => triggerCoverLetter(job.id))}
                      className="rounded bg-gray-700 hover:bg-gray-600 px-2 py-1 text-xs"
                      title="Cover Letter"
                    >✉️</button>
                    <button
                      onClick={() => dispatch("Interview prep", () => triggerInterview(job.id))}
                      className="rounded bg-gray-700 hover:bg-gray-600 px-2 py-1 text-xs"
                      title="Interview Prep"
                    >🎓</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
