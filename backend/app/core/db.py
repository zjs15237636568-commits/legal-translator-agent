"""
SQLite 访问层（基于 aiosqlite）。
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiosqlite

from .config import DB_FILE

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  source_name   TEXT,
  source_type   TEXT,
  created_at    INTEGER,
  updated_at    INTEGER,
  llm_provider  TEXT,
  llm_model     TEXT,
  status        TEXT
);

CREATE TABLE IF NOT EXISTS segments (
  id            TEXT PRIMARY KEY,
  project_id    TEXT NOT NULL,
  seq           INTEGER,
  clause_no     TEXT,
  heading       TEXT,
  original_md   TEXT,
  token_count   INTEGER,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_segments_project ON segments(project_id, seq);

CREATE TABLE IF NOT EXISTS translations (
  segment_id    TEXT PRIMARY KEY,
  translated_md TEXT,
  status        TEXT,
  error         TEXT,
  retry_count   INTEGER DEFAULT 0,
  updated_at    INTEGER,
  FOREIGN KEY (segment_id) REFERENCES segments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS risks (
  id            TEXT PRIMARY KEY,
  project_id    TEXT NOT NULL,
  segment_id    TEXT,
  level         TEXT,
  category      TEXT,
  title         TEXT,
  detail        TEXT,
  suggestion    TEXT,
  created_at    INTEGER,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_risks_project ON risks(project_id);

CREATE TABLE IF NOT EXISTS qa_messages (
  id            TEXT PRIMARY KEY,
  project_id    TEXT NOT NULL,
  role          TEXT,
  content       TEXT,
  citations     TEXT,
  created_at    INTEGER,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_qa_project ON qa_messages(project_id, created_at);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_FILE) as db:
        await db.executescript(SCHEMA)
        await db.commit()


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect(DB_FILE)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        await db.close()


def now_ms() -> int:
    return int(time.time() * 1000)
