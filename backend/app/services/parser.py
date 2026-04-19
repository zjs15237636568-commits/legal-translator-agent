"""
文件解析：docx / pdf → Markdown。

设计原则：
- 尽量保留标题层级（通过字体大小启发式或 Word 的 Heading 样式）
- 保留段落换行
- 表格转为 Markdown 表格
- 列表转为 Markdown 列表
"""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph
import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------
_HEADING_RE = re.compile(r"^Heading\s+(\d+)$", re.IGNORECASE)


def _docx_iter_blocks(doc: Document) -> Iterable:
    """按文档流顺序迭代段落和表格。"""
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield DocxTable(child, doc)


def _paragraph_to_md(p: Paragraph) -> str:
    text = (p.text or "").rstrip()
    if not text:
        return ""
    style = (p.style.name or "") if p.style else ""
    m = _HEADING_RE.match(style)
    if m:
        level = min(int(m.group(1)), 6)
        return f"{'#' * level} {text}"
    if style.lower().startswith("title"):
        return f"# {text}"
    # 列表（简单启发式）
    if style.lower().startswith("list"):
        return f"- {text}"
    return text


def _table_to_md(tbl: DocxTable) -> str:
    rows = []
    for row in tbl.rows:
        cells = [re.sub(r"\s+", " ", c.text).strip() for c in row.cells]
        rows.append(cells)
    if not rows:
        return ""
    header = rows[0]
    sep = ["---"] * len(header)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    for r in rows[1:]:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def parse_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    lines: list[str] = []
    for block in _docx_iter_blocks(doc):
        if isinstance(block, Paragraph):
            md = _paragraph_to_md(block)
            if md:
                lines.append(md)
                lines.append("")
        elif isinstance(block, DocxTable):
            md = _table_to_md(block)
            if md:
                lines.append(md)
                lines.append("")
    return "\n".join(lines).strip() + "\n"


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
def parse_pdf(data: bytes) -> str:
    """PDF 基础转 Markdown：按字号启发式识别标题。"""
    doc = fitz.open(stream=data, filetype="pdf")
    # 收集全文字号，推断标题阈值
    sizes: list[float] = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    sizes.append(span["size"])
    if not sizes:
        return ""
    sizes_sorted = sorted(set(round(s, 1) for s in sizes), reverse=True)
    # 前 3 个最大字号作为 H1/H2/H3 阈值
    heading_sizes = sizes_sorted[:3]

    def _size_to_level(size: float) -> int | None:
        for i, hs in enumerate(heading_sizes):
            if abs(size - hs) < 0.3 and hs > (sizes_sorted[3] if len(sizes_sorted) > 3 else 0):
                return i + 1
        return None

    lines: list[str] = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                if not line.get("spans"):
                    continue
                text = "".join(s["text"] for s in line["spans"]).strip()
                if not text:
                    continue
                # 取该行最大字号
                max_size = max(s["size"] for s in line["spans"])
                level = _size_to_level(max_size)
                if level:
                    lines.append(f"{'#' * level} {text}")
                else:
                    lines.append(text)
            lines.append("")  # 段落间空行
    doc.close()
    # 去重多余空行
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return out.strip() + "\n"


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------
def parse_to_markdown(filename: str, data: bytes) -> tuple[str, str]:
    """
    返回 (markdown_text, source_type)
    source_type: 'docx' | 'pdf'
    """
    suffix = Path(filename).suffix.lower()
    if suffix in (".docx",):
        return parse_docx(data), "docx"
    if suffix == ".pdf":
        return parse_pdf(data), "pdf"
    raise ValueError(f"Unsupported file type: {suffix}. Only .docx and .pdf are supported.")
