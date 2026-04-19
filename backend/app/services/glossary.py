"""
术语库管理 + 匹配器。

设计：
- 文件：./data/glossary.json
- 匹配：整词（\b 边界），大小写不敏感
- 不做语境/领域判断（决策：交由大模型）
"""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from app.core.config import GLOSSARY_FILE


@dataclass
class Term:
    en: str
    zh: str
    note: str = ""


_lock = threading.Lock()
_cache_mtime: float = -1
_cache_terms: list[Term] = []
_cache_pattern: re.Pattern | None = None


def _load_from_disk() -> list[Term]:
    if not GLOSSARY_FILE.exists():
        return []
    try:
        raw = json.loads(GLOSSARY_FILE.read_text(encoding="utf-8"))
        return [Term(**item) for item in raw if item.get("en") and item.get("zh")]
    except Exception:
        return []


def _save_to_disk(terms: list[Term]) -> None:
    GLOSSARY_FILE.write_text(
        json.dumps([asdict(t) for t in terms], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_pattern(terms: list[Term]) -> re.Pattern | None:
    if not terms:
        return None
    # 长词优先，避免短词覆盖长词
    keys = sorted({t.en for t in terms}, key=len, reverse=True)
    escaped = [re.escape(k) for k in keys]
    pat = r"\b(?:" + "|".join(escaped) + r")\b"
    return re.compile(pat, re.IGNORECASE)


def _refresh_cache() -> None:
    global _cache_mtime, _cache_terms, _cache_pattern
    mtime = GLOSSARY_FILE.stat().st_mtime if GLOSSARY_FILE.exists() else 0
    if mtime == _cache_mtime and _cache_pattern is not None:
        return
    with _lock:
        if mtime == _cache_mtime and _cache_pattern is not None:
            return
        _cache_terms = _load_from_disk()
        _cache_pattern = _build_pattern(_cache_terms)
        _cache_mtime = mtime


# ---------------------------------------------------------------------------
# 对外 API
# ---------------------------------------------------------------------------
def list_terms() -> list[Term]:
    _refresh_cache()
    return list(_cache_terms)


def replace_all(terms: list[Term]) -> list[Term]:
    # 去重（按 en 小写）
    seen: dict[str, Term] = {}
    for t in terms:
        key = t.en.strip().lower()
        if not key or not t.zh.strip():
            continue
        seen[key] = Term(en=t.en.strip(), zh=t.zh.strip(), note=(t.note or "").strip())
    cleaned = list(seen.values())
    _save_to_disk(cleaned)
    _refresh_cache()
    return cleaned


def upsert(term: Term) -> list[Term]:
    terms = list_terms()
    key = term.en.strip().lower()
    found = False
    for i, t in enumerate(terms):
        if t.en.strip().lower() == key:
            terms[i] = term
            found = True
            break
    if not found:
        terms.append(term)
    return replace_all(terms)


def delete(en: str) -> list[Term]:
    terms = [t for t in list_terms() if t.en.strip().lower() != en.strip().lower()]
    return replace_all(terms)


def find_matches(text: str) -> list[Term]:
    """返回 text 中命中的术语（去重）。"""
    _refresh_cache()
    if not _cache_pattern:
        return []
    hits = {m.group(0).lower() for m in _cache_pattern.finditer(text)}
    if not hits:
        return []
    by_en = {t.en.lower(): t for t in _cache_terms}
    result: list[Term] = []
    seen = set()
    for h in hits:
        t = by_en.get(h)
        if t and t.en.lower() not in seen:
            result.append(t)
            seen.add(t.en.lower())
    return result


def format_for_prompt(terms: list[Term]) -> str:
    """命中的术语渲染为 Prompt 片段。"""
    if not terms:
        return ""
    lines = [f'- "{t.en}" → "{t.zh}"' + (f"  // {t.note}" if t.note else "") for t in terms]
    return "\n".join(lines)
