from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.services.translator import stream_translate_project, retry_segment

router = APIRouter(prefix="/api", tags=["translate"])


@router.get("/projects/{project_id}/translate/stream")
async def translate_stream(project_id: str):
    async def event_gen():
        async for ev in stream_translate_project(project_id):
            yield ev
    return EventSourceResponse(event_gen())


@router.post("/segments/{segment_id}/retry")
async def segment_retry(segment_id: str):
    try:
        return await retry_segment(segment_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
