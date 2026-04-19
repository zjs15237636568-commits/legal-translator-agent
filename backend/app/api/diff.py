from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import DiffRequest
from app.services.diff import diff_projects

router = APIRouter(prefix="/api", tags=["diff"])


@router.post("/diff")
async def diff(body: DiffRequest):
    if body.left_project_id == body.right_project_id:
        raise HTTPException(400, "Two different projects are required")
    try:
        items = await diff_projects(body.left_project_id, body.right_project_id)
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(500, str(e))
