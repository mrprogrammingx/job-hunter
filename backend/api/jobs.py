import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import get_optional_user
from backend.db.models import User
from core.database import get_all_jobs, get_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(user: Optional[User] = Depends(get_optional_user)):
    user_id = user.id if user else None
    return [j.to_dict() for j in get_all_jobs(user_id=user_id)]


@router.get("/{job_id}")
async def get_job_by_id(job_id: int):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()
