from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services import risk

router = APIRouter(prefix="/api/projects", tags=["risks"])


@router.post("/{project_id}/risks/scan")
async def scan(project_id: str):
    try:
        items = await risk.scan_project(project_id)
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{project_id}/risks")
async def list_risks(project_id: str):
    items = await risk.list_project_risks(project_id)
    return {"items": items, "total": len(items)}
