"use client";

import { useState } from "react";
import { AgentStatusCard } from "@/components/AgentStatusCard";
import { TaskStream } from "@/components/TaskStream";
import { triggerHunt, triggerAnalyze, getTasks } from "@/lib/api";
import type { Task } from "@/lib/types";

export default function Dashboard() {
  const [roles, setRoles] = useState("Data Engineer");
  const [keywords, setKeywords] = useState("Python, Airflow, dbt");
  const [location, setLocation] = useState("Remote");
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);

  async function refreshTasks() {
    setTasks(await getTasks());
  }

  async function handleHunt() {
    const res = await triggerHunt({
      roles: roles.split(",").map((r) => r.trim()),
      keywords: keywords.split(",").map((k) => k.trim()),
      location,
      experience_level: "mid",
    });
    setActiveTaskId(res.task_id);
    await refreshTasks();
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Trigger agents and monitor their progress in real time.</p>
      </div>

      {/* Hunt panel */}
      <section className="rounded-xl border border-gray-700 bg-gray-800 p-6 space-y-4">
        <h2 className="font-semibold text-lg">🔍 Hunt for Jobs</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Target Roles</label>
            <input
              className="w-full rounded bg-gray-700 border border-gray-600 px-3 py-2 text-sm"
              value={roles}
              onChange={(e) => setRoles(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Keywords</label>
            <input
              className="w-full rounded bg-gray-700 border border-gray-600 px-3 py-2 text-sm"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Location</label>
            <input
              className="w-full rounded bg-gray-700 border border-gray-600 px-3 py-2 text-sm"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
        </div>
        <button
          onClick={handleHunt}
          className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Start Hunt
        </button>

        {activeTaskId && (
          <div className="mt-4">
            <p className="text-xs text-gray-400 mb-2">Live agent stream · task {activeTaskId.slice(0, 8)}…</p>
            <TaskStream
              taskId={activeTaskId}
              onDone={() => refreshTasks()}
            />
          </div>
        )}
      </section>

      {/* Recent tasks */}
      {tasks.length > 0 && (
        <section>
          <h2 className="font-semibold text-lg mb-4">Recent Agent Runs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tasks.slice(0, 6).map((t) => (
              <AgentStatusCard key={t.id} task={t} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
