from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.llm_config import LLMConfig
from schemas.llm_config import LLMConfigCreate, LLMConfigResponse

router = APIRouter(prefix="/api/llm-configs", tags=["llm-configs"])


@router.get("", response_model=list[LLMConfigResponse])
async def list_llm_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMConfig).order_by(LLMConfig.created_at.desc()))
    configs = result.scalars().all()
    return configs


@router.post("", response_model=LLMConfigResponse, status_code=201)
async def create_llm_config(body: LLMConfigCreate, db: AsyncSession = Depends(get_db)):
    config = LLMConfig(
        name=body.name,
        provider=body.provider,
        model=body.model,
        api_key_encrypted=body.api_key_encrypted,
        base_url=body.base_url,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        is_default=body.is_default,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return config
