"""
版本比对：
- 输入：两个 project_id（均为英文原文已解析/分段）
- 逻辑：段落级语义对齐 → 逐对交给 LLM 生成差异 + 业务影响
- MVP：先用 difflib 粗对齐 + LLM 精修
"""
from __future__ import annotations

import difflib
import json
import re
from typing import Any

from app.core.db import get_db
from app.services.llm import get_provider

DIFF_SYSTEM_PROMPT = """You compare two versions of a cross-border legal contract.

Given paired segments (left = old, right = new), return a strict JSON array where each item is:
{
  "type": "added" | "removed" | "modified" | "unchanged",
  "left_id": string | null,
  "right_id": string | null,
  "summary_zh": short Chinese summary of the change (1-2 sentences),
  "business_impact_zh": Chinese business impact note (1-2 sentences, or "" if unchanged)
}

Rules:
- Output the JSON array only. No fences, no commentary.
- Skip "unchanged" items to keep output concise (unless the user explicitly wants full view).
- Use Simplified Chinese for summary_zh and business_impact_zh.
""".strip()


async def _load_segments(project_id: str) -> list[dict]:
    async with get_db() as db:
        cur = await db.execute(
            "SELECT id, seq, clause_no, original_md FROM segments "
            "WHERE project_id = ? ORDER BY seq ASC",
            (project_id,),
        )
        return [dict(r) for r in await cur.fetchall()]


def _align(left: list[dict], right: list[dict]) -> list[tuple[dict | None, dict | None]]:
    """基于 clause_no 优先 + difflib 兜底做对齐。"""
    pairs: list[tuple[dict | None, dict | None]] = []
    right_by_clause = {r["clause_no"]: r for r in right if r.get("clause_no")}
    used_right: set[str] = set()

    remaining_left: list[dict] = []
    for l in left:
        if l.get("clause_no") and l["clause_no"] in right_by_clause:
            r = right_by_clause[l["clause_no"]]
            pairs.append((l, r))
            used_right.add(r["id"])
        else:
            remaining_left.append(l)

    remaining_right = [r for r in right if r["id"] not in used_right]

    # 对剩余部分按文本相似度配对（贪心）
    left_texts = [l["original_md"] for l in remaining_left]
    right_texts = [r["original_md"] for r in remaining_right]
    matched_right: set[int] = set()

    for i, lt in enumerate(left_texts):
        best_j = -1
        best_ratio = 0.0
        for j, rt in enumerate(right_texts):
            if j in matched_right:
                continue
            ratio = difflib.SequenceMatcher(None, lt, rt, autojunk=False).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_j = j
        if best_j >= 0 and best_ratio >= 0.4:
            pairs.append((remaining_left[i], remaining_right[best_j]))
            matched_right.add(best_j)
        else:
            pairs.append((remaining_left[i], None))

    for j, rt in enumerate(right_texts):
        if j not in matched_right:
            pairs.append((None, remaining_right[j]))

    # 按左序号排序（None 放末尾）
    pairs.sort(key=lambda p: (p[0]["seq"] if p[0] else 10**9, p[1]["seq"] if p[1] else 10**9))
    return pairs


def _extract_json_array(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    return []


async def diff_projects(left_id: str, right_id: str) -> list[dict]:
    provider = get_provider()
    left = await _load_segments(left_id)
    right = await _load_segments(right_id)
    pairs = _align(left, right)

    # 准备 LLM 输入（过滤纯相同）
    payload = []
    for l, r in pairs:
        if l and r and l["original_md"].strip() == r["original_md"].strip():
            continue  # 相同，跳过
        payload.append(
            {
                "left_id": l["id"] if l else None,
                "right_id": r["id"] if r else None,
                "left_text": (l["original_md"] if l else ""),
                "right_text": (r["original_md"] if r else ""),
            }
        )

    if not payload:
        return []

    # 分批（避免超长）
    BATCH = 8
    all_items: list[dict] = []
    for i in range(0, len(payload), BATCH):
        batch = payload[i : i + BATCH]
        user_msg = "Compare these segment pairs:\n\n" + json.dumps(batch, ensure_ascii=False)
        try:
            content = await provider.chat(
                [
                    {"role": "system", "content": DIFF_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=3000,
            )
            items = _extract_json_array(content)
            for it in items:
                if not isinstance(it, dict):
                    continue
                t = (it.get("type") or "").lower()
                if t not in ("added", "removed", "modified", "unchanged"):
                    continue
                all_items.append(
                    {
                        "type": t,
                        "left_id": it.get("left_id"),
                        "right_id": it.get("right_id"),
                        "summary_zh": (it.get("summary_zh") or "").strip(),
                        "business_impact_zh": (it.get("business_impact_zh") or "").strip(),
                    }
                )
        except Exception:
            continue

    return all_items
