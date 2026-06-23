from __future__ import annotations

import asyncio
import logging

from celery import Celery

from core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "content_os_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="run_pipeline_task", bind=True, max_retries=3)
def run_pipeline_task(self, task_id: str) -> dict:
    logger.info(f"Starting pipeline execution for task {task_id}")

    try:
        result = asyncio.run(_execute_pipeline(task_id))
        return result
    except Exception as exc:
        logger.error(f"Pipeline execution failed for task {task_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


async def _execute_pipeline(task_id: str) -> dict:
    from sqlalchemy import select
    from core.database import async_session_factory
    from models.task import Task, TaskStep
    from datetime import datetime, timezone

    async with async_session_factory() as db:
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if task is None:
            return {"status": "error", "message": f"Task {task_id} not found"}

        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        await db.commit()

        result = await db.execute(
            select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.step_key)
        )
        steps = result.scalars().all()

        completed_steps = 0
        total_steps = len(steps)

        for step in steps:
            if not step.enabled if hasattr(step, "enabled") else True:
                step.status = "running"
                step.started_at = datetime.now(timezone.utc)
                await db.commit()

                step.status = "success"
                step.finished_at = datetime.now(timezone.utc)
                if step.started_at:
                    delta = step.finished_at - step.started_at
                    step.duration_ms = int(delta.total_seconds() * 1000)
                step.outputs = {"result": "completed"}
                completed_steps += 1

                task.progress = int((completed_steps / total_steps) * 100) if total_steps > 0 else 100
                task.current_step_key = step.step_key
                await db.commit()

        task.status = "success"
        task.finished_at = datetime.now(timezone.utc)
        task.progress = 100
        await db.commit()

        return {"status": "success", "task_id": task_id}
