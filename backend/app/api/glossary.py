from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import TermDTO, TermListDTO
from app.services import glossary as gloss

router = APIRouter(prefix="/api/glossary", tags=["glossary"])


@router.get("", response_model=TermListDTO)
async def list_all():
    items = gloss.list_terms()
    return TermListDTO(items=[TermDTO(**t.__dict__) for t in items])


@router.put("", response_model=TermListDTO)
async def replace_all(body: TermListDTO):
    terms = [gloss.Term(**t.model_dump()) for t in body.items]
    saved = gloss.replace_all(terms)
    return TermListDTO(items=[TermDTO(**t.__dict__) for t in saved])


@router.post("", response_model=TermListDTO)
async def upsert(body: TermDTO):
    saved = gloss.upsert(gloss.Term(**body.model_dump()))
    return TermListDTO(items=[TermDTO(**t.__dict__) for t in saved])


class DeleteBody(BaseModel):
    en: str


@router.delete("", response_model=TermListDTO)
async def delete(body: DeleteBody):
    saved = gloss.delete(body.en)
    return TermListDTO(items=[TermDTO(**t.__dict__) for t in saved])
