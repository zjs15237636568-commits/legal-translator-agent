"""
智能三级分段器：Clause/Section → 段落 → Token（必要时按句子切分）。

返回的每个 Segment 为前端的锚点单元。
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_ENC.encode(text))
except Exception:  # pragma: no cover
    def count_tokens(text: str) -> int:
        # 粗略回退：英文 4 char ≈ 1 token
        return max(1, len(text) // 4)


MAX_TOKEN = 1500
OVERLAP_TOKEN = 200

# Clause 编号识别：3.1 / 3.1.2 / Article 3 / Clause 3.1 / Section 3
_CLAUSE_RE = re.compile(
    r"""^\s*(?:
        (?P<num>\d+(?:\.\d+){0,3})\s+        |   # 3  / 3.1 / 3.1.2
        (?:Article|Clause|Section)\s+
            (?P<named>\d+(?:\.\d+){0,3})\s*[.:\-]?\s+
    )""",
    re.VERBOSE | re.IGNORECASE,
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_SENTENCE_SPLIT = re.compile(r"(?<=[\.\!\?。！？；;])\s+")


@dataclass
class Segment:
    id: str
    seq: int
    clause_no: str | None
    heading: str | None
    original_md: str
    token_count: int = 0

    @staticmethod
    def new_id(seq: int) -> str:
        return f"seg_{seq:04d}_{uuid.uuid4().hex[:6]}"


def _extract_clause_no(text: str) -> str | None:
    m = _CLAUSE_RE.match(text)
    if not m:
        return None
    return m.group("num") or m.group("named")


def _split_block_by_tokens(block: str) -> list[str]:
    """单 block 超大时按句子切，带 overlap。"""
    if count_tokens(block) <= MAX_TOKEN:
        return [block]
    sentences = _SENTENCE_SPLIT.split(block)
    chunks: list[str] = []
    cur: list[str] = []
    cur_tokens = 0
    for s in sentences:
        t = count_tokens(s)
        if cur_tokens + t > MAX_TOKEN and cur:
            chunks.append(" ".join(cur).strip())
            # overlap
            overlap: list[str] = []
            overlap_tokens = 0
            for prev in reversed(cur):
                pt = count_tokens(prev)
                if overlap_tokens + pt > OVERLAP_TOKEN:
                    break
                overlap.insert(0, prev)
                overlap_tokens += pt
            cur = overlap + [s]
            cur_tokens = overlap_tokens + t
        else:
            cur.append(s)
            cur_tokens += t
    if cur:
        chunks.append(" ".join(cur).strip())
    return [c for c in chunks if c]


def segment_markdown(md: str) -> list[Segment]:
    """
    主分段流程：
    1. 先按标题拆 Section，保留标题所在行
    2. Section 内按空行拆 block
    3. 超大 block 按句子 + overlap 切
    """
    lines = md.splitlines()
    # Step 1: 按标题切 section
    sections: list[tuple[str | None, list[str]]] = []  # (heading, body_lines)
    current_heading: str | None = None
    current_body: list[str] = []

    for line in lines:
        if _HEADING_RE.match(line):
            if current_heading is not None or current_body:
                sections.append((current_heading, current_body))
            current_heading = line.strip()
            current_body = []
        else:
            current_body.append(line)
    sections.append((current_heading, current_body))

    segments: list[Segment] = []
    seq = 0

    for heading, body in sections:
        # 将 heading 作为独立 segment（便于锚点/TOC）
        if heading:
            clause = _extract_clause_no(re.sub(r"^#+\s+", "", heading))
            seg = Segment(
                id=Segment.new_id(seq),
                seq=seq,
                clause_no=clause,
                heading=heading,
                original_md=heading,
            )
            seg.token_count = count_tokens(seg.original_md)
            segments.append(seg)
            seq += 1

        # body 按空行拆 block
        blocks: list[str] = []
        buf: list[str] = []
        for ln in body:
            if ln.strip() == "":
                if buf:
                    blocks.append("\n".join(buf).strip())
                    buf = []
            else:
                buf.append(ln)
        if buf:
            blocks.append("\n".join(buf).strip())

        for block in blocks:
            if not block:
                continue
            for chunk in _split_block_by_tokens(block):
                clause = _extract_clause_no(chunk)
                seg = Segment(
                    id=Segment.new_id(seq),
                    seq=seq,
                    clause_no=clause,
                    heading=None,
                    original_md=chunk,
                )
                seg.token_count = count_tokens(seg.original_md)
                segments.append(seg)
                seq += 1

    return segments
