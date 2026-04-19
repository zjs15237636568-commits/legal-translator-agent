"""Pydantic schema 统一定义。"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class TermDTO(BaseModel):
    en: str
    zh: str
    note: str = ""


class TermListDTO(BaseModel):
    items: list[TermDTO]


class ProviderDTO(BaseModel):
    api_key: str = ""
    base_url: str = ""
    model: str = ""


class ConfigDTO(BaseModel):
    active_provider: str
    providers: dict[str, ProviderDTO]


class QARequest(BaseModel):
    question: str


class DiffRequest(BaseModel):
    left_project_id: str
    right_project_id: str


class ProjectSummary(BaseModel):
    id: str
    name: str
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    created_at: int
    updated_at: int
    status: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class SegmentDTO(BaseModel):
    id: str
    seq: int
    clause_no: Optional[str] = None
    heading: Optional[str] = None
    original_md: str
    token_count: int
    translated_md: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
