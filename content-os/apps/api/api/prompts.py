from __future__ import annotations

import uuid
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.prompt import Prompt, PromptVersion
from models.user import User
from schemas.prompt import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptVersionCreate,
    PromptVersionResponse,
    PromptDryRunRequest,
)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


async def _get_default_owner_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        return user.id
    return uuid.UUID("00000000-0000-0000-0000-000000000000")


@router.get("", response_model=List[PromptResponse])
async def list_prompts(
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Prompt)
        .options(selectinload(Prompt.current_version))
        .order_by(Prompt.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if category:
        stmt = stmt.where(Prompt.category == category)
    result = await db.execute(stmt)
    prompts = result.unique().scalars().all()
    return prompts


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt(body: PromptCreate, db: AsyncSession = Depends(get_db)):
    owner_id = await _get_default_owner_id(db)

    prompt = Prompt(
        owner_id=owner_id,
        name=body.name,
        description=body.description,
        category=body.category,
    )
    db.add(prompt)
    await db.flush()

    if body.initial_version:
        version = PromptVersion(
            prompt_id=prompt.id,
            content=body.initial_version.content,
            variables_schema=body.initial_version.variables_schema,
            output_schema=body.initial_version.output_schema,
            model_hint=body.initial_version.model_hint,
            changelog=body.initial_version.changelog,
            version=1,
        )
        db.add(version)
        await db.flush()
        prompt.current_version_id = version.id
        await db.flush()

    result = await db.execute(
        select(Prompt)
        .options(selectinload(Prompt.current_version))
        .where(Prompt.id == prompt.id)
    )
    return result.unique().scalar_one()


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: uuid.UUID,
    body: PromptUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Prompt).options(selectinload(Prompt.current_version)).where(Prompt.id == prompt_id)
    )
    prompt = result.unique().scalar_one_or_none()
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prompt, key, value)

    await db.flush()

    result = await db.execute(
        select(Prompt).options(selectinload(Prompt.current_version)).where(Prompt.id == prompt_id)
    )
    return result.unique().scalar_one()


@router.post("/{prompt_id}/dry-run")
async def dry_run_prompt(
    prompt_id: uuid.UUID,
    body: PromptDryRunRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if prompt.current_version_id is None:
        raise HTTPException(status_code=400, detail="Prompt has no current version")

    version_result = await db.execute(
        select(PromptVersion).where(PromptVersion.id == prompt.current_version_id)
    )
    version = version_result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=400, detail="Prompt version not found")

    rendered = _render_template(version.content, body.variables)

    return {
        "prompt_id": str(prompt.id),
        "version": version.version,
        "rendered_content": rendered,
        "variables_used": body.variables,
        "model_hint": body.model_hint or version.model_hint,
    }


@router.post("/{prompt_id}/render")
async def render_prompt(
    prompt_id: uuid.UUID,
    body: PromptDryRunRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    prompt = result.scalar_one_or_none()
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if prompt.current_version_id is None:
        raise HTTPException(status_code=400, detail="Prompt has no current version")

    version_result = await db.execute(
        select(PromptVersion).where(PromptVersion.id == prompt.current_version_id)
    )
    version = version_result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=400, detail="Prompt version not found")

    rendered = _render_template(version.content, body.variables)

    return {"rendered_content": rendered}


def _render_template(template: str, variables: dict) -> str:
    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))

    return re.sub(r"\{\{(\w+)\}\}", replace_var, template)
