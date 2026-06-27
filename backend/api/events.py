"""
SSE endpoint — streams real-time agent progress to the frontend.

The client connects once and receives a stream of JSON events until
the task completes. Each event is a TaskState snapshot or a band_event
(raw agent-to-agent message from the EventBand).
"""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.queue.manager import task_manager

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/{task_id}")
async def stream(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def generator():
        q = task.event_queue
        while True:
            try:
                event = q.get_nowait()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("done"):
                    break
            except Exception:
                # Queue empty — yield a heartbeat and wait
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.3)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # nginx: disable buffering
        },
    )
