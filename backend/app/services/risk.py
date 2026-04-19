"""
风险扫描：全文一次性投喂 LLM，返回结构化风险 JSON。
MVP：纯 LLM，无规则库。
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from app.core.db import get_db, now_ms
from app.services.llm import get_provider

BATCH_SEGMENT_TOKENS = 3000  # 每批累计 token 上限，避免超上下文

RISK_SYSTEM_PROMPT = """You are a senior cross-border legal & business risk reviewer.

Given a set of contract segments (each with a segment_id and original English text),
identify potential risks and return a STRICT JSON array.

Risk levels:
- "red":    legal breach, unenforceable clause, regulatory non-compliance, unfair obligation, one-sided indemnity, unlimited liability, etc.
- "yellow": business feasibility concerns (SLA tightness, settlement timing like T+0, system capacity, data flow, FX lock, localization compliance, etc.)

Each item MUST have these fields:
- segment_id: string (exact id from input)
- level: "red" | "yellow"
- category: short string (e.g., "Jurisdiction", "Data Compliance", "Settlement", "IP", "Liability")
- title: short string (≤ 30 chars, Simplified Chinese)
- detail: 1-3 sentences describing the risk (Simplified Chinese)
- suggestion: 1-2 sentences actionable advice (Simplified Chinese)

Rules:
- Output ONLY the JSON array. No markdown fence. No commentary.
- If no risks found in the batch, output: []
- Do NOT invent segment_ids.
""".strip()


def _extract_json_array(text: str) -> list[dict]:
    text = text.strip()
    # 去除可能的 ```json fence
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    # 尝试从首个 '[' 到最后一个 ']' 截取
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            return []
    return []


def _batch_segments(rows: list[dict], max_tokens: int = BATCH_SEGMENT_TOKENS) -> list[list[dict]]:
    batches: list[list[dict]] = []
    cur: list[dict] = []
    cur_tokens = 0
    for r in rows:
        t = r.get("token_count") or max(1, len(r["original_md"]) // 4)
        if cur and cur_tokens + t > max_tokens:
            batches.append(cur)
            cur, cur_tokens = [], 0
        cur.append(r)
        cur_tokens += t
    if cur:
        batches.append(cur)
    return batches


async def scan_project(project_id: str) -> list[dict]:
    provider = get_provider()

    async with get_db() as db:
        cur = await db.execute(
            "SELECT id, seq, original_md, token_count FROM segments "
            "WHERE project_id = ? ORDER BY seq ASC",
            (project_id,),
        )
        rows = [dict(r) for r in await cur.fetchall()]

    if not rows:
        return []

    batches = _batch_segments(rows)
    all_risks: list[dict] = []

    for batch in batches:
        payload = [{"segment_id": r["id"], "text": r["original_md"]} for r in batch]
        user_msg = (
            "Review these segments and list the risks in JSON array:\n\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        try:
            content = await provider.chat(
                [
                    {"role": "system", "content": RISK_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=4096,
            )
        except Exception as e:
            # 单批失败，跳过
            continue
        items = _extract_json_array(content)
        valid_ids = {r["id"] for r in batch}
        for it in items:
            if not isinstance(it, dict):
                continue
            sid = it.get("segment_id")
            level = (it.get("level") or "").lower()
            if sid not in valid_ids or level not in ("red", "yellow"):
                continue
            all_risks.append(
                {
                    "id": f"risk_{uuid.uuid4().hex[:10]}",
                    "project_id": project_id,
                    "segment_id": sid,
                    "level": level,
                    "category": (it.get("category") or "").strip()[:40],
                    "title": (it.get("title") or "").strip()[:60],
                    "detail": (it.get("detail") or "").strip(),
                    "suggestion": (it.get("suggestion") or "").strip(),
                    "created_at": now_ms(),
                }
            )

    # 持久化：清理旧的再写新的
    async with get_db() as db:
        await db.execute("DELETE FROM risks WHERE project_id = ?", (project_id,))
        await db.executemany(
            """INSERT INTO risks(id, project_id, segment_id, level, category,
               title, detail, suggestion, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    r["id"], r["project_id"], r["segment_id"], r["level"],
                    r["category"], r["title"], r["detail"], r["suggestion"],
                    r["created_at"],
                )
                for r in all_risks
            ],
        )
        await db.commit()

    return all_risks


async def list_project_risks(project_id: str) -> list[dict]:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT * FROM risks WHERE project_id = ? ORDER BY "
            "CASE level WHEN 'red' THEN 0 ELSE 1 END, created_at ASC",
            (project_id,),
        )
        return [dict(r) for r in await cur.fetchall()]
