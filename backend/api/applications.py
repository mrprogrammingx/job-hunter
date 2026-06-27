import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.auth import get_optional_user
from backend.db.models import User
from core.database import get_all_applications, update_application_status

router = APIRouter(prefix="/api/applications", tags=["applications"])


class StatusUpdate(BaseModel):
    status: str
    notes: str = ""


@router.get("")
async def list_applications(user: Optional[User] = Depends(get_optional_user)):
    user_id = user.id if user else None
    return get_all_applications(user_id=user_id)


@router.patch("/{job_id}")
async def update_status(job_id: int, body: StatusUpdate):
    valid = {"discovered", "applied", "interview", "offer", "accepted", "rejected"}
    if body.status not in valid:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(valid)}")
    update_application_status(job_id, body.status, body.notes)
    return {"job_id": job_id, "status": body.status}
