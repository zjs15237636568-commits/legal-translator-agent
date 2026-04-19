from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import QARequest
from app.services import qa

router = APIRouter(prefix="/api/projects", tags=["qa"])


@router.post("/{project_id}/qa")
async def ask(project_id: str, body: QARequest):
    if not body.question.strip():
        raise HTTPException(400, "Question is empty")
    try:
        return await qa.ask(project_id, body.question.strip())
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{project_id}/qa/history")
async def history(project_id: str):
    return {"items": await qa.list_history(project_id)}
