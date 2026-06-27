"""
Agent trigger endpoints.

Each POST creates a task, dispatches the agent to a thread (non-blocking),
and immediately returns a task_id + stream URL so the client can follow
progress via SSE.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.queue.manager import task_manager
from backend.queue import tasks as agent_tasks

router = APIRouter(prefix="/api/agents", tags=["agents"])
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent-worker")


def _dispatch(fn, *args) -> dict:
    """Create a task, run fn(*args) in the thread pool, return task info."""
    agent_name = fn.__name__.replace("run_", "")
    task = task_manager.create(agent=agent_name)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, fn, task.id, *args)
    return {"task_id": task.id, "agent": agent_name, "stream_url": f"/api/events/{task.id}"}


# ── Request schemas ──────────────────────────────────────────────────────────

class HuntRequest(BaseModel):
    roles: list[str] = ["Software Engineer"]
    keywords: list[str] = ["Python"]
    location: str = "Remote"
    experience_level: str = "mid"


class AnalyzeRequest(BaseModel):
    resume_path: str


class ScoreRequest(BaseModel):
    job_ids: list[int]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/hunt")
async def trigger_hunt(body: HuntRequest):
    return _dispatch(agent_tasks.run_hunt, body.roles, body.keywords, body.location, body.experience_level)


@router.post("/analyze")
async def trigger_analyze(body: AnalyzeRequest):
    return _dispatch(agent_tasks.run_analyze, body.resume_path)


@router.post("/score")
async def trigger_score(body: ScoreRequest):
    return _dispatch(agent_tasks.run_score, body.job_ids)


@router.post("/tailor/{job_id}")
async def trigger_tailor(job_id: int):
    return _dispatch(agent_tasks.run_tailor, job_id)


@router.post("/cover-letter/{job_id}")
async def trigger_cover_letter(job_id: int):
    return _dispatch(agent_tasks.run_cover_letter, job_id)


@router.post("/interview/{job_id}")
async def trigger_interview(job_id: int):
    return _dispatch(agent_tasks.run_interview, job_id)


@router.get("/tasks")
async def list_tasks():
    return [t.to_dict() for t in task_manager.all()]


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()
