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


# FIX: _execute_pipeline now delegates to PipelineEngine instead of
# reimplementing a broken version that marks all steps as "success"
# without actually executing any step logic.
async def _execute_pipeline(task_id: str) -> dict:
    from core.database import async_session_factory
    from core.event_bus import EventBus
    from core.pipeline_engine import PipelineEngine
    from core.step_registry import StepRegistry
    from uuid import UUID

    event_bus = EventBus(settings.REDIS_URL)

    async with async_session_factory() as db:
        engine = PipelineEngine(
            db_session=db,
            step_registry=StepRegistry,
            event_bus=event_bus,
            storage=None,
        )
        try:
            await engine.run_task(UUID(task_id))
            return {"status": "success", "task_id": task_id}
        except Exception as exc:
            logger.error(f"PipelineEngine execution failed for task {task_id}: {exc}")
            return {"status": "failed", "task_id": task_id, "error": str(exc)}
        finally:
            await event_bus.close()


@celery_app.task(name="run_pipeline_task", bind=True, max_retries=3)
def run_pipeline_task(self, task_id: str) -> dict:
    logger.info(f"Starting pipeline execution for task {task_id}")

    try:
        result = asyncio.run(_execute_pipeline(task_id))
        return result
    except Exception as exc:
        logger.error(f"Pipeline execution failed for task {task_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)
