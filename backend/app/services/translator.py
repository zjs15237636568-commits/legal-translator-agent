"""
翻译服务：
- 段落并发 = 3
- SSE 事件：segment_start / segment_delta / segment_done / segment_error / all_done
- 支持重试、断点续翻（从 DB 读取 status != 'done' 的段落）
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import AsyncIterator

import aiosqlite

from app.core.db import get_db, now_ms
from app.services import glossary
from app.services.llm import get_provider, LLMConfigError

MAX_CONCURRENCY = 3
MAX_RETRY = 3


TRANSLATION_SYSTEM_PROMPT = """You are a senior cross-border legal counsel translator.
Target language: Simplified Chinese.

Principles:
- Preserve Markdown structure, headings (#/##/###), lists, tables, emphasis, and inline code.
- Maintain legal rigor: no omission, no paraphrasing of obligations.
- Use formal Chinese legal register (e.g., "应当", "不得", "经...同意").
- Keep clause numbers and cross-references verbatim (e.g., "Clause 3.1" → "第3.1条" but numbers unchanged).
- Keep party names, product names, and defined terms in their original form unless a fixed translation is provided below.

Return ONLY the translated Markdown. No commentary, no extra blank lines, no wrapping code fences.
""".strip()


def _build_messages(original_md: str) -> list[dict]:
    hits = glossary.find_matches(original_md)
    glossary_block = glossary.format_for_prompt(hits)
    system = TRANSLATION_SYSTEM_PROMPT
    if glossary_block:
        system += (
            "\n\nFixed glossary (use these translations EXACTLY when the English term appears):\n"
            + glossary_block
        )
    user = f"Translate the following legal Markdown to Simplified Chinese:\n\n{original_md}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
async def _list_pending_segments(db: aiosqlite.Connection, project_id: str) -> list[aiosqlite.Row]:
    """返回需要翻译的段落（无译文记录 或 status != done）。"""
    cur = await db.execute(
        """
        SELECT s.id, s.seq, s.original_md, IFNULL(t.status, 'pending') as tstatus,
               IFNULL(t.retry_count, 0) as retry_count
        FROM segments s
        LEFT JOIN translations t ON t.segment_id = s.id
        WHERE s.project_id = ?
        ORDER BY s.seq ASC
        """,
        (project_id,),
    )
    rows = await cur.fetchall()
    return [r for r in rows if r["tstatus"] != "done"]


async def _mark_status(
    db: aiosqlite.Connection,
    segment_id: str,
    *,
    status: str,
    translated: str | None = None,
    error: str | None = None,
    inc_retry: bool = False,
) -> None:
    # Upsert translations
    await db.execute(
        """
        INSERT INTO translations(segment_id, translated_md, status, error, retry_count, updated_at)
        VALUES (?, ?, ?, ?, 0, ?)
        ON CONFLICT(segment_id) DO UPDATE SET
          translated_md = COALESCE(excluded.translated_md, translations.translated_md),
          status = excluded.status,
          error  = excluded.error,
          retry_count = translations.retry_count + (CASE WHEN ? THEN 1 ELSE 0 END),
          updated_at = excluded.updated_at
        """,
        (segment_id, translated, status, error, now_ms(), 1 if inc_retry else 0),
    )
    await db.commit()


# ---------------------------------------------------------------------------
# 单段翻译
# ---------------------------------------------------------------------------
@dataclass
class SegmentEvent:
    event: str
    data: dict

    def as_sse(self) -> dict:
        return {"event": self.event, "data": json.dumps(self.data, ensure_ascii=False)}


async def _translate_one(
    provider,
    segment_id: str,
    original_md: str,
    out_queue: asyncio.Queue,
    sem: asyncio.Semaphore,
) -> None:
    async with sem:
        await out_queue.put(SegmentEvent("segment_start", {"segment_id": segment_id}))
        # 简单重试
        last_err: Exception | None = None
        for attempt in range(MAX_RETRY):
            try:
                buffer: list[str] = []
                async for delta in provider.stream_chat(
                    _build_messages(original_md),
                    temperature=0.1,
                    max_tokens=4096,
                ):
                    buffer.append(delta)
                    await out_queue.put(
                        SegmentEvent(
                            "segment_delta",
                            {"segment_id": segment_id, "delta": delta},
                        )
                    )
                full = "".join(buffer).strip()
                async with get_db() as db:
                    await _mark_status(db, segment_id, status="done", translated=full)
                await out_queue.put(
                    SegmentEvent(
                        "segment_done",
                        {"segment_id": segment_id, "full_text": full},
                    )
                )
                return
            except Exception as e:
                last_err = e
                # 指数退避
                await asyncio.sleep(min(2 ** attempt, 8))

        # 失败
        err_msg = f"{type(last_err).__name__}: {last_err}"
        async with get_db() as db:
            await _mark_status(
                db, segment_id, status="failed", error=err_msg, inc_retry=True
            )
        await out_queue.put(
            SegmentEvent(
                "segment_error",
                {"segment_id": segment_id, "error": err_msg},
            )
        )


# ---------------------------------------------------------------------------
# 项目级流式翻译
# ---------------------------------------------------------------------------
async def stream_translate_project(project_id: str) -> AsyncIterator[dict]:
    """异步生成 SSE 事件 dict，供 sse-starlette 消费。"""
    try:
        provider = get_provider()
    except LLMConfigError as e:
        yield {"event": "fatal", "data": json.dumps({"error": str(e)})}
        return

    async with get_db() as db:
        rows = await _list_pending_segments(db, project_id)
        # 把所有待翻译段落预置为 pending
        for row in rows:
            await _mark_status(db, row["id"], status="pending")

    if not rows:
        yield {"event": "all_done", "data": json.dumps({"total": 0, "duration_ms": 0})}
        return

    start = time.time()
    queue: asyncio.Queue = asyncio.Queue()
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def _runner():
        tasks = [
            asyncio.create_task(
                _translate_one(provider, r["id"], r["original_md"], queue, sem)
            )
            for r in rows
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        await queue.put(None)  # 哨兵

    runner_task = asyncio.create_task(_runner())

    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item.as_sse()
    finally:
        await runner_task

    duration = int((time.time() - start) * 1000)
    yield {
        "event": "all_done",
        "data": json.dumps({"total": len(rows), "duration_ms": duration}),
    }


# ---------------------------------------------------------------------------
# 单段重试（非 SSE）
# ---------------------------------------------------------------------------
async def retry_segment(segment_id: str) -> dict:
    provider = get_provider()
    async with get_db() as db:
        cur = await db.execute("SELECT original_md FROM segments WHERE id = ?", (segment_id,))
        row = await cur.fetchone()
        if not row:
            raise ValueError("Segment not found")
        original = row["original_md"]
        await _mark_status(db, segment_id, status="pending", inc_retry=True)

    full = ""
    async for delta in provider.stream_chat(
        _build_messages(original),
        temperature=0.1,
        max_tokens=4096,
    ):
        full += delta
    full = full.strip()

    async with get_db() as db:
        await _mark_status(db, segment_id, status="done", translated=full)
    return {"segment_id": segment_id, "translated_md": full}
