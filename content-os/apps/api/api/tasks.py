from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.task import Task, TaskStep
from models.pipeline import Pipeline
from schemas.task import TaskCreate, TaskResponse, TaskStepResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Task).options(selectinload(Task.steps)).order_by(Task.created_at.desc()).offset(offset).limit(limit)
    if status:
        stmt = stmt.where(Task.status == status)
    result = await db.execute(stmt)
    tasks = result.unique().scalars().all()
    return tasks


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Pipeline).options(selectinload(Pipeline.steps)).where(Pipeline.id == body.pipeline_id)
    )
    pipeline = result.unique().scalar_one_or_none()
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    task = Task(
        pipeline_id=body.pipeline_id,
        owner_id=pipeline.owner_id,
        title=body.title or pipeline.name,
        inputs=body.inputs,
        status="queued",
    )
    db.add(task)
    await db.flush()

    for step in pipeline.steps:
        task_step = TaskStep(
            task_id=task.id,
            step_key=step.step_key,
            step_type=step.step_type,
            status="pending",
            config_snapshot=step.config or {},
            inputs={},
            outputs={},
        )
        db.add(task_step)

    await db.flush()
    await db.refresh(task)

    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task.id)
    )
    task = result.unique().scalar_one()
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    task = result.unique().scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    task = result.unique().scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in ("failed", "paused"):
        raise HTTPException(status_code=400, detail="Task is not in a retryable state")

    task.status = "queued"
    task.error = None

    for step in task.steps:
        if step.status == "failed":
            step.status = "pending"
            step.error = None
            step.stack_trace = None

    await db.flush()
    await db.refresh(task)

    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    return result.unique().scalar_one()


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    task = result.unique().scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in ("queued", "running", "paused"):
        raise HTTPException(status_code=400, detail="Task cannot be canceled in its current state")

    task.status = "canceled"
    task.finished_at = datetime.now(timezone.utc)

    for step in task.steps:
        if step.status in ("pending", "running"):
            step.status = "skipped"

    await db.flush()
    await db.refresh(task)

    result = await db.execute(
        select(Task).options(selectinload(Task.steps)).where(Task.id == task_id)
    )
    return result.unique().scalar_one()


@router.post("/{task_id}/steps/{step_key}/run", response_model=TaskStepResponse)
async def run_single_step(
    task_id: uuid.UUID,
    step_key: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task_id, TaskStep.step_key == step_key)
    )
    step = result.scalar_one_or_none()
    if step is None:
        raise HTTPException(status_code=404, detail="Task step not found")

    step.status = "running"
    step.started_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(step)
    return step


@router.get("/{task_id}/steps/{step_key}/artifact")
async def get_step_artifact(
    task_id: uuid.UUID,
    step_key: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task_id, TaskStep.step_key == step_key)
    )
    step = result.scalar_one_or_none()
    if step is None:
        raise HTTPException(status_code=404, detail="Task step not found")

    return {"step_key": step.step_key, "step_type": step.step_type, "outputs": step.outputs}
