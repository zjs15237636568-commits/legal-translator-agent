from __future__ import annotations

import uuid
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import load_config
from app.core.db import get_db, now_ms
from app.models.schemas import ProjectSummary, SegmentDTO
from app.services.parser import parse_to_markdown
from app.services.segmenter import segment_markdown

router = APIRouter(prefix="/api/projects", tags=["projects"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/upload", response_model=ProjectSummary)
async def upload_project(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds 20MB limit")

    try:
        md, source_type = parse_to_markdown(file.filename or "unknown", data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Parse failed: {e}")

    segs = segment_markdown(md)
    if not segs:
        raise HTTPException(400, "No content extracted from file")

    cfg = load_config()
    active = cfg.get_active()
    project_id = f"prj_{uuid.uuid4().hex[:10]}"
    ts = now_ms()

    async with get_db() as db:
        await db.execute(
            """INSERT INTO projects(id, name, source_name, source_type, created_at,
               updated_at, llm_provider, llm_model, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                project_id,
                file.filename or "Untitled",
                file.filename,
                source_type,
                ts, ts,
                cfg.active_provider,
                active.model,
                "parsed",
            ),
        )
        await db.executemany(
            """INSERT INTO segments(id, project_id, seq, clause_no, heading,
               original_md, token_count) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (s.id, project_id, s.seq, s.clause_no, s.heading,
                 s.original_md, s.token_count)
                for s in segs
            ],
        )
        await db.commit()

    return ProjectSummary(
        id=project_id,
        name=file.filename or "Untitled",
        source_name=file.filename,
        source_type=source_type,
        created_at=ts, updated_at=ts,
        status="parsed",
        llm_provider=cfg.active_provider,
        llm_model=active.model,
    )


@router.get("", response_model=list[ProjectSummary])
async def list_projects():
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        )
        rows = await cur.fetchall()
    return [ProjectSummary(**dict(r)) for r in rows]


@router.get("/{project_id}", response_model=ProjectSummary)
async def get_project(project_id: str):
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cur.fetchone()
    if not row:
        raise HTTPException(404, "Project not found")
    return ProjectSummary(**dict(row))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    async with get_db() as db:
        await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
    return {"ok": True}


@router.get("/{project_id}/segments", response_model=list[SegmentDTO])
async def list_segments(project_id: str):
    async with get_db() as db:
        cur = await db.execute(
            """SELECT s.*, t.translated_md, t.status as tstatus, t.error
               FROM segments s LEFT JOIN translations t ON t.segment_id = s.id
               WHERE s.project_id = ? ORDER BY s.seq ASC""",
            (project_id,),
        )
        rows = await cur.fetchall()
    result = []
    for r in rows:
        d = dict(r)
        result.append(
            SegmentDTO(
                id=d["id"], seq=d["seq"], clause_no=d.get("clause_no"),
                heading=d.get("heading"), original_md=d["original_md"],
                token_count=d["token_count"], translated_md=d.get("translated_md"),
                status=d.get("tstatus"), error=d.get("error"),
            )
        )
    return result
