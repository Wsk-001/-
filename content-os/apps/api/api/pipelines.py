from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.pipeline import Pipeline, PipelineStep
from models.user import User
from schemas.pipeline import (
    PipelineCreate,
    PipelineUpdate,
    PipelineResponse,
    PipelineStepCreate,
    PipelineStepUpdate,
    PipelineStepResponse,
)

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])


async def _get_default_owner_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        return user.id
    return uuid.UUID("00000000-0000-0000-0000-000000000000")


@router.get("", response_model=list[PipelineResponse])
async def list_pipelines(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Pipeline)
        .options(selectinload(Pipeline.steps))
        .order_by(Pipeline.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    pipelines = result.unique().scalars().all()
    return pipelines


@router.post("", response_model=PipelineResponse, status_code=201)
async def create_pipeline(body: PipelineCreate, db: AsyncSession = Depends(get_db)):
    owner_id = await _get_default_owner_id(db)

    pipeline = Pipeline(
        owner_id=owner_id,
        name=body.name,
        description=body.description,
        template_key=body.template_key,
        is_default=body.is_default,
    )
    db.add(pipeline)
    await db.flush()

    for step_data in body.steps:
        step = PipelineStep(
            pipeline_id=pipeline.id,
            step_key=step_data.step_key,
            step_type=step_data.step_type,
            name=step_data.name,
            display_order=step_data.display_order,
            config=step_data.config,
            prompt_id=step_data.prompt_id,
            llm_config_id=step_data.llm_config_id,
            depends_on=step_data.depends_on,
            enabled=step_data.enabled,
            retry_policy=step_data.retry_policy,
        )
        db.add(step)

    await db.flush()

    result = await db.execute(
        select(Pipeline).options(selectinload(Pipeline.steps)).where(Pipeline.id == pipeline.id)
    )
    return result.unique().scalar_one()


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Pipeline).options(selectinload(Pipeline.steps)).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.unique().scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: uuid.UUID,
    body: PipelineUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Pipeline).options(selectinload(Pipeline.steps)).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.unique().scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pipeline, key, value)

    await db.flush()

    result = await db.execute(
        select(Pipeline).options(selectinload(Pipeline.steps)).where(Pipeline.id == pipeline_id)
    )
    return result.unique().scalar_one()


@router.post("/{pipeline_id}/steps", response_model=PipelineStepResponse, status_code=201)
async def create_pipeline_step(
    pipeline_id: uuid.UUID,
    body: PipelineStepCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    step = PipelineStep(
        pipeline_id=pipeline_id,
        step_key=body.step_key,
        step_type=body.step_type,
        name=body.name,
        display_order=body.display_order,
        config=body.config,
        prompt_id=body.prompt_id,
        llm_config_id=body.llm_config_id,
        depends_on=body.depends_on,
        enabled=body.enabled,
        retry_policy=body.retry_policy,
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


@router.put("/{pipeline_id}/steps/{step_key}", response_model=PipelineStepResponse)
async def update_pipeline_step(
    pipeline_id: uuid.UUID,
    step_key: str,
    body: PipelineStepUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PipelineStep).where(
            PipelineStep.pipeline_id == pipeline_id,
            PipelineStep.step_key == step_key,
        )
    )
    step = result.scalar_one_or_none()
    if step is None:
        raise HTTPException(status_code=404, detail="Pipeline step not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(step, key, value)

    await db.flush()
    await db.refresh(step)
    return step


@router.delete("/{pipeline_id}/steps/{step_key}", status_code=204)
async def delete_pipeline_step(
    pipeline_id: uuid.UUID,
    step_key: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PipelineStep).where(
            PipelineStep.pipeline_id == pipeline_id,
            PipelineStep.step_key == step_key,
        )
    )
    step = result.scalar_one_or_none()
    if step is None:
        raise HTTPException(status_code=404, detail="Pipeline step not found")

    await db.delete(step)
    await db.flush()
