"""
Q&A with Citations (RAG - BM25 检索 + 强制引用格式).
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from rank_bm25 import BM25Okapi

from app.core.db import get_db, now_ms
from app.services.llm import get_provider

TOP_K = 6

QA_SYSTEM_PROMPT = """You are a senior cross-border legal counsel assistant.

Answer the user's question based ONLY on the provided contract segments below.

Rules:
- Answer in Simplified Chinese.
- Every factual claim MUST be followed by a citation in one of these forms:
  * [Clause 3.1] when a clause number is available
  * [§12] when no clause number, referring to paragraph sequence
- Do not cite segments you did not use.
- If the answer is not contained in the segments, explicitly say:
  "根据提供的合同内容，未找到直接相关条款。" and optionally suggest what might help.
- Be concise and professional.
""".strip()


def _tokenize(text: str) -> list[str]:
    # 英文按单词，中文按字；足够 BM25 使用
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text)
    return tokens


async def _load_segments(project_id: str) -> list[dict]:
    async with get_db() as db:
        cur = await db.execute(
            """SELECT s.id, s.seq, s.clause_no, s.heading, s.original_md,
                      t.translated_md
               FROM segments s
               LEFT JOIN translations t ON t.segment_id = s.id
               WHERE s.project_id = ?
               ORDER BY s.seq ASC""",
            (project_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


def _retrieve(segments: list[dict], question: str, k: int = TOP_K) -> list[dict]:
    if not segments:
        return []
    docs: list[list[str]] = []
    for s in segments:
        combined = (s["original_md"] or "") + "\n" + (s.get("translated_md") or "")
        docs.append(_tokenize(combined))
    bm25 = BM25Okapi(docs)
    scores = bm25.get_scores(_tokenize(question))
    scored = list(zip(scores, segments))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for sc, s in scored[:k] if sc > 0]


def _build_context(top: list[dict]) -> str:
    parts = []
    for s in top:
        ref = f"[Clause {s['clause_no']}]" if s.get("clause_no") else f"[§{s['seq']}]"
        parts.append(
            f"SEGMENT_ID: {s['id']}\nREF: {ref}\n"
            f"ENGLISH:\n{s['original_md']}\n"
            f"CHINESE:\n{s.get('translated_md') or '(not translated yet)'}\n"
            "---"
        )
    return "\n".join(parts)


# 解析 assistant 输出里出现的 citations，用于前端跳转
_CITATION_RE = re.compile(r"\[(?:Clause\s+([\d\.]+)|§(\d+))\]", re.IGNORECASE)


def _parse_citations(answer: str, top: list[dict]) -> list[dict]:
    """根据 top 候选集把 answer 中的 [Clause X.X]/[§N] 映射回 segment_id。"""
    # 两个索引：clause_no → segment / seq → segment
    by_clause = {s["clause_no"]: s for s in top if s.get("clause_no")}
    by_seq = {str(s["seq"]): s for s in top}
    citations: list[dict] = []
    seen_ids: set[str] = set()
    for m in _CITATION_RE.finditer(answer):
        clause = m.group(1)
        seq = m.group(2)
        seg = None
        if clause and clause in by_clause:
            seg = by_clause[clause]
        elif seq and seq in by_seq:
            seg = by_seq[seq]
        if seg and seg["id"] not in seen_ids:
            seen_ids.add(seg["id"])
            citations.append(
                {
                    "segment_id": seg["id"],
                    "clause_no": seg.get("clause_no"),
                    "seq": seg["seq"],
                    "label": m.group(0),
                }
            )
    return citations


async def ask(project_id: str, question: str) -> dict:
    provider = get_provider()
    segments = await _load_segments(project_id)
    top = _retrieve(segments, question)

    if not top:
        context = "(No relevant segments found.)"
    else:
        context = _build_context(top)

    user_msg = (
        f"Question: {question}\n\n"
        f"Contract segments (use these only):\n\n{context}"
    )
    answer = await provider.chat(
        [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
        max_tokens=2048,
    )

    citations = _parse_citations(answer, top)

    # 持久化消息
    async with get_db() as db:
        await db.execute(
            "INSERT INTO qa_messages(id, project_id, role, content, citations, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (f"msg_{uuid.uuid4().hex[:10]}", project_id, "user", question, "[]", now_ms()),
        )
        await db.execute(
            "INSERT INTO qa_messages(id, project_id, role, content, citations, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                f"msg_{uuid.uuid4().hex[:10]}", project_id, "assistant",
                answer, json.dumps(citations, ensure_ascii=False), now_ms(),
            ),
        )
        await db.commit()

    return {"answer": answer, "citations": citations}


async def list_history(project_id: str) -> list[dict]:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT id, role, content, citations, created_at FROM qa_messages "
            "WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        )
        rows = [dict(r) for r in await cur.fetchall()]
        for r in rows:
            try:
                r["citations"] = json.loads(r["citations"] or "[]")
            except Exception:
                r["citations"] = []
        return rows
