"""
In-memory task manager.

Agents run synchronously in a thread pool. This manager bridges them to
the async FastAPI world via a regular (thread-safe) queue per task, which
the SSE generator drains asynchronously.

To swap in Celery: replace `create()` / `_run_in_thread()` with Celery
task dispatch, and replace `event_queue` with a Redis pub/sub channel.
"""

import queue as sync_queue
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class TaskState:
    id: str
    agent: str
    status: str = "queued"
    progress: int = 0
    message: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    # Thread-safe queue consumed by the SSE generator
    event_queue: sync_queue.Queue = field(default_factory=sync_queue.Queue)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
        }


class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, TaskState] = {}

    def create(self, agent: str) -> TaskState:
        task = TaskState(id=str(uuid4()), agent=agent)
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Optional[TaskState]:
        return self._tasks.get(task_id)

    def all(self) -> list[TaskState]:
        return sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)

    def update(self, task_id: str, **kwargs) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        for k, v in kwargs.items():
            setattr(task, k, v)
        # Push a snapshot to the per-task SSE queue
        task.event_queue.put_nowait({**task.to_dict(), "done": False})

    def finish(self, task_id: str, result: Any = None) -> None:
        self.update(task_id, status="done", progress=100, result=result)
        task = self._tasks.get(task_id)
        if task:
            task.event_queue.put_nowait({**task.to_dict(), "done": True})

    def fail(self, task_id: str, error: str) -> None:
        self.update(task_id, status="failed", error=error)
        task = self._tasks.get(task_id)
        if task:
            task.event_queue.put_nowait({**task.to_dict(), "done": True})


# Singleton — shared across all requests in a single process
task_manager = TaskManager()
