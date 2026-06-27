"""
Agent trigger endpoints.

Each POST creates a task, dispatches the agent to a thread (non-blocking),
and immediately returns a task_id + stream URL so the client can follow
progress via SSE.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.auth import get_optional_user
from backend.db.models import User
from backend.queue.manager import task_manager
from backend.queue import tasks as agent_tasks

router = APIRouter(prefix="/api/agents", tags=["agents"])
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="agent-worker")


def _dispatch(fn, *args, user_id: Optional[int] = None) -> dict:
    """Create a task, run fn(*args) in the thread pool, return task info."""
    agent_name = fn.__name__.replace("run_", "")
    task = task_manager.create(agent=agent_name, user_id=user_id)
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
async def trigger_hunt(body: HuntRequest, user: Optional[User] = Depends(get_optional_user)):
    uid = user.id if user else None
    return _dispatch(
        agent_tasks.run_hunt,
        body.roles, body.keywords, body.location, body.experience_level, uid,
        user_id=uid,
    )


@router.post("/analyze")
async def trigger_analyze(body: AnalyzeRequest, user: Optional[User] = Depends(get_optional_user)):
    return _dispatch(agent_tasks.run_analyze, body.resume_path, user_id=user.id if user else None)


@router.post("/score")
async def trigger_score(body: ScoreRequest, user: Optional[User] = Depends(get_optional_user)):
    return _dispatch(agent_tasks.run_score, body.job_ids, user_id=user.id if user else None)


@router.post("/tailor/{job_id}")
async def trigger_tailor(job_id: int, user: Optional[User] = Depends(get_optional_user)):
    return _dispatch(agent_tasks.run_tailor, job_id, user_id=user.id if user else None)


@router.post("/cover-letter/{job_id}")
async def trigger_cover_letter(job_id: int, user: Optional[User] = Depends(get_optional_user)):
    return _dispatch(agent_tasks.run_cover_letter, job_id, user_id=user.id if user else None)


@router.post("/interview/{job_id}")
async def trigger_interview(job_id: int, user: Optional[User] = Depends(get_optional_user)):
    return _dispatch(agent_tasks.run_interview, job_id, user_id=user.id if user else None)


@router.get("/tasks")
async def list_tasks(user: Optional[User] = Depends(get_optional_user)):
    tasks = task_manager.all()
    if user:
        tasks = [t for t in tasks if t.user_id is None or t.user_id == user.id]
    return [t.to_dict() for t in tasks]


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()
