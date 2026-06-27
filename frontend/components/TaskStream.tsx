"use client";

import { useEffect, useState } from "react";
import type { SSEEvent } from "@/lib/types";

interface Props {
  taskId: string;
  onDone?: (result: unknown) => void;
}

export function TaskStream({ taskId, onDone }: Props) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("queued");

  useEffect(() => {
    const es = new EventSource(`/api/events/${taskId}`);

    es.onmessage = (e) => {
      const event: SSEEvent = JSON.parse(e.data);
      setEvents((prev) => [...prev.slice(-49), event]); // keep last 50

      if (event.progress !== undefined) setProgress(event.progress);
      if (event.status) setStatus(event.status);
      if (event.done) {
        es.close();
        onDone?.(event.result);
      }
    };

    es.onerror = () => es.close();
    return () => es.close();
  }, [taskId, onDone]);

  const statusColor: Record<string, string> = {
    queued: "text-gray-400",
    running: "text-blue-400",
    done: "text-green-400",
    failed: "text-red-400",
  };

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-900 p-4 font-mono text-sm">
      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className={statusColor[status] ?? "text-gray-400"}>{status.toUpperCase()}</span>
          <span className="text-gray-400">{progress}%</span>
        </div>
        <div className="h-1.5 w-full rounded bg-gray-700">
          <div
            className="h-1.5 rounded bg-blue-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Event log */}
      <div className="max-h-48 overflow-y-auto space-y-1">
        {events.map((ev, i) => (
          <div key={i} className="text-xs text-gray-400">
            {ev.type === "band_event" ? (
              <span>
                <span className="text-purple-400">[{ev.sender}]</span>{" "}
                <span className="text-yellow-400">{ev.msg_type}</span>
              </span>
            ) : (
              <span className={statusColor[ev.status ?? ""] ?? "text-gray-400"}>
                {ev.message}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
