from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.exporter import export_bilingual_docx

router = APIRouter(prefix="/api/projects", tags=["export"])


@router.get("/{project_id}/export/docx")
async def export_docx(project_id: str):
    try:
        data = await export_bilingual_docx(project_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

    headers = {
        "Content-Disposition": f'attachment; filename="bilingual_{project_id}.docx"',
    }
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )
