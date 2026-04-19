"""
FastAPI 入口。
运行：
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8765
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    config as config_api,
    diff as diff_api,
    export as export_api,
    glossary as glossary_api,
    projects as projects_api,
    qa as qa_api,
    risks as risks_api,
    translate as translate_api,
)
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Legal Translator & Risk Review",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"ok": True}


# 路由注册
app.include_router(config_api.router)
app.include_router(glossary_api.router)
app.include_router(projects_api.router)
app.include_router(translate_api.router)
app.include_router(risks_api.router)
app.include_router(qa_api.router)
app.include_router(diff_api.router)
app.include_router(export_api.router)
