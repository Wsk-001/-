from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.event_bus import EventBus
from core.step_registry import StepRegistry


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class StepContext:
    """Context passed to each step executor."""

    task_id: UUID
    inputs: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Result from a step executor."""

    outputs: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)


@dataclass
class _StepRuntime:
    """Combined runtime view of a TaskStep and its PipelineStep template.

    TaskStep holds runtime state (status, outputs, attempt, etc.) while
    PipelineStep holds the template (display_order, depends_on, enabled,
    retry_policy, prompt_id, llm_config_id).  They are matched by step_key.
    """

    task_step: Any
    pipeline_step: Any | None = None


class ArtifactStorage:
    """Minimal storage interface for persisting large artifacts.

    Implementations should provide async ``save`` and ``load`` methods.
    The engine calls these opportunistically; if ``storage`` is ``None``
    the calls are skipped and artifacts stay in memory only.
    """

    async def save(self, task_id: UUID, name: str, content: str | bytes) -> str:
        raise NotImplementedError

    async def load(self, task_id: UUID, name: str) -> str | bytes:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Pipeline engine
# ---------------------------------------------------------------------------


class PipelineEngine:
    """Orchestrates pipeline execution with DAG-based step scheduling.

    The engine loads a Task and its TaskSteps from the database, merges each
    TaskStep with its corresponding PipelineStep template (for display_order,
    depends_on, enabled, retry_policy), builds a DAG, and executes steps in
    topological order.  Artifacts are passed between steps in memory and
    persisted in ``TaskStep.outputs`` under the ``_artifacts`` key.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        step_registry: type[StepRegistry],
        event_bus: EventBus,
        storage: ArtifactStorage | None = None,
    ) -> None:
        self.db_session = db_session
        self.step_registry = step_registry
        self.event_bus = event_bus
        self.storage = storage

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_task(self, task_id: UUID, resume_from_step: str | None = None) -> None:
        """Execute a pipeline task.

        Steps:
            1. Load task + task steps (merged with pipeline step templates).
            2. Build DAG from depends_on.
            3. Topological sort.
            4. Execute each enabled step in order.
            5. Pass artifacts between steps.
            6. Update task/step status in DB.
            7. Emit events via event_bus.
            8. Handle failures with retry.
        """
        task = await self._load_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        # Mark task as running.
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        task.error = None
        await self.db_session.commit()
        await self._emit("task.started", task_id, {"task_id": str(task_id)})

        try:
            steps = await self._load_steps(task)
            ordered_steps = self._build_dag(steps)

            # Shared artifact store accumulated across steps.
            artifacts: dict[str, Any] = {}

            # If resuming, load artifacts from already-completed steps.
            start_index = 0
            if resume_from_step is not None:
                start_index = self._find_resume_index(ordered_steps, resume_from_step)
                self._restore_artifacts(ordered_steps[:start_index], artifacts)

            total_steps = sum(1 for s in ordered_steps if self._step_enabled(s))
            completed_steps = 0

            for index in range(start_index, len(ordered_steps)):
                step = ordered_steps[index]
                if not self._step_enabled(step):
                    continue

                task.current_step_key = self._step_key(step)
                await self.db_session.commit()

                await self._execute_step_with_retry(task_id, step, artifacts)

                completed_steps += 1
                if total_steps > 0:
                    task.progress = int((completed_steps / total_steps) * 100)
                await self.db_session.commit()

            task.status = "success"
            task.finished_at = datetime.now(timezone.utc)
            task.progress = 100
            await self.db_session.commit()
            await self._emit("task.completed", task_id, {"task_id": str(task_id)})
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            task.finished_at = datetime.now(timezone.utc)
            await self.db_session.commit()
            await self._emit(
                "task.failed",
                task_id,
                {"task_id": str(task_id), "error": str(exc)},
            )
            raise

    async def run_single_step(self, task_id: UUID, step_key: str) -> StepResult:
        """Run a single step for debugging (not part of main pipeline flow).

        Loads artifacts produced by previously-completed steps from the DB
        and executes only the requested step.  The step's status is **not**
        persisted; this is a dry-run style helper.
        """
        task = await self._load_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        steps = await self._load_steps(task)
        ordered_steps = self._build_dag(steps)

        target = next((s for s in ordered_steps if self._step_key(s) == step_key), None)
        if target is None:
            raise ValueError(f"Step '{step_key}' not found in task {task_id}")

        # Reconstruct artifacts from prior completed steps.
        artifacts: dict[str, Any] = {}
        for step in ordered_steps:
            if self._step_key(step) == step_key:
                break
            if self._step_status(step) == "success":
                self._merge_step_artifacts(step, artifacts)

        executor = self.step_registry.get(self._step_type(target))()
        ctx = StepContext(
            task_id=task_id,
            inputs={},
            config=self._build_step_config(target),
            artifacts=artifacts,
        )
        return await executor.execute(ctx)

    # ------------------------------------------------------------------
    # DAG construction
    # ------------------------------------------------------------------

    def _build_dag(self, steps: list[_StepRuntime]) -> list[_StepRuntime]:
        """Build execution order from depends_on.

        Performs a topological sort using depth-first traversal, falling
        back to ``display_order`` for deterministic tie-breaking.  Raises
        ``ValueError`` if a circular dependency is detected.
        """
        step_map = {self._step_key(s): s for s in steps}
        visited: set[str] = set()
        in_progress: set[str] = set()
        order: list[_StepRuntime] = []

        def visit(step_key: str) -> None:
            if step_key in visited:
                return
            if step_key in in_progress:
                raise ValueError(f"Circular dependency detected at step '{step_key}'")
            step = step_map.get(step_key)
            if step is None:
                return
            in_progress.add(step_key)
            for dep in self._step_depends_on(step):
                visit(dep)
            in_progress.discard(step_key)
            visited.add(step_key)
            order.append(step)

        # Sort by display_order first so independent steps have a stable order.
        sorted_steps = sorted(steps, key=lambda s: self._step_display_order(s))
        for step in sorted_steps:
            visit(self._step_key(step))
        return order

    @staticmethod
    def _find_resume_index(steps: list[_StepRuntime], resume_from_step: str) -> int:
        """Return the index of the step to resume from."""
        for index, step in enumerate(steps):
            if PipelineEngine._step_key(step) == resume_from_step:
                return index
        raise ValueError(f"Step '{resume_from_step}' not found for resume")

    # ------------------------------------------------------------------
    # Step execution with retry
    # ------------------------------------------------------------------

    async def _execute_step_with_retry(
        self,
        task_id: UUID,
        step: _StepRuntime,
        artifacts: dict[str, Any],
    ) -> None:
        """Execute a single step, retrying on failure up to max_retries."""
        max_retries = self._step_max_retries(step)
        attempt = self._step_attempt(step)

        while True:
            try:
                await self._execute_step_once(task_id, step, artifacts, attempt)
                return
            except Exception as exc:  # noqa: BLE001
                attempt += 1
                if attempt <= max_retries + 1:
                    # Update attempt count and retry.
                    step.task_step.attempt = attempt
                    await self.db_session.commit()
                    await self._emit(
                        "step.retrying",
                        task_id,
                        {
                            "step_key": self._step_key(step),
                            "attempt": attempt,
                            "max_retries": max_retries,
                            "error": str(exc),
                        },
                    )
                    continue
                raise

    async def _execute_step_once(
        self,
        task_id: UUID,
        step: _StepRuntime,
        artifacts: dict[str, Any],
        attempt: int,
    ) -> None:
        """Execute a single step attempt."""
        ts = step.task_step
        step_key = self._step_key(step)

        # Mark step as running.
        ts.status = "running"
        ts.started_at = datetime.now(timezone.utc)
        ts.attempt = attempt
        ts.error = None
        ts.stack_trace = None
        await self.db_session.commit()
        await self._emit(
            "step.started",
            task_id,
            {"step_key": step_key, "attempt": attempt},
        )

        start_time = time.monotonic()
        try:
            executor_cls = self.step_registry.get(self._step_type(step))
            executor = executor_cls()
            ctx = StepContext(
                task_id=task_id,
                inputs={},
                config=self._build_step_config(step),
                artifacts=artifacts,
            )
            result = await executor.execute(ctx)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            # Merge artifacts into the shared store for downstream steps.
            artifacts.update(result.artifacts)

            # Persist outputs + artifacts to DB (artifacts embedded in outputs).
            stored_outputs = dict(result.outputs)
            stored_outputs["_artifacts"] = result.artifacts
            stored_outputs["_metrics"] = result.metrics

            ts.status = "success"
            ts.outputs = stored_outputs
            ts.duration_ms = duration_ms
            ts.finished_at = datetime.now(timezone.utc)
            ts.error = None
            await self.db_session.commit()
            await self._emit(
                "step.completed",
                task_id,
                {
                    "step_key": step_key,
                    "duration_ms": duration_ms,
                    "outputs": result.outputs,
                },
            )
        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.monotonic() - start_time) * 1000)
            ts.status = "failed"
            ts.error = str(exc)
            ts.stack_trace = traceback.format_exc()
            ts.duration_ms = duration_ms
            ts.finished_at = datetime.now(timezone.utc)
            await self.db_session.commit()
            await self._emit(
                "step.failed",
                task_id,
                {
                    "step_key": step_key,
                    "error": str(exc),
                    "duration_ms": duration_ms,
                },
            )
            raise

    # ------------------------------------------------------------------
    # Step config builder
    # ------------------------------------------------------------------

    def _build_step_config(self, step: _StepRuntime) -> dict[str, Any]:
        """Build step config, merging prompt_id and llm_config_id from PipelineStep.

        The TaskStep's ``config_snapshot`` is the base config (copied from the
        PipelineStep at task creation time).  We additionally merge
        ``prompt_id`` and ``llm_config_id`` from the live PipelineStep so that
        steps like ``generate_article`` can resolve them from the DB.
        """
        config: dict[str, Any] = dict(self._step_config(step))
        ps = step.pipeline_step
        if ps is not None:
            if ps.prompt_id is not None:
                config.setdefault("prompt_id", str(ps.prompt_id))
            if ps.llm_config_id is not None:
                config.setdefault("llm_config_id", str(ps.llm_config_id))
        return config

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    async def _load_task(self, task_id: UUID) -> Any:
        from models.task import Task

        result = await self.db_session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def _load_steps(self, task: Any) -> list[_StepRuntime]:
        """Load TaskSteps and merge with PipelineSteps by step_key."""
        from models.task import TaskStep
        from models.pipeline import PipelineStep

        # Load TaskSteps.
        result = await self.db_session.execute(
            select(TaskStep).where(TaskStep.task_id == task.id)
        )
        task_steps = list(result.scalars().all())

        # Load PipelineSteps for the task's pipeline.
        result = await self.db_session.execute(
            select(PipelineStep).where(PipelineStep.pipeline_id == task.pipeline_id)
        )
        pipeline_steps = list(result.scalars().all())

        # Match by step_key.
        ps_map = {ps.step_key: ps for ps in pipeline_steps}
        merged: list[_StepRuntime] = []
        for ts in task_steps:
            ps = ps_map.get(ts.step_key)
            merged.append(_StepRuntime(task_step=ts, pipeline_step=ps))
        return merged

    # ------------------------------------------------------------------
    # Artifact restoration
    # ------------------------------------------------------------------

    def _restore_artifacts(
        self,
        completed_steps: list[_StepRuntime],
        artifacts: dict[str, Any],
    ) -> None:
        """Load artifacts from already-completed steps into the shared store."""
        for step in completed_steps:
            if self._step_status(step) == "success":
                self._merge_step_artifacts(step, artifacts)

    @staticmethod
    def _merge_step_artifacts(step: _StepRuntime, artifacts: dict[str, Any]) -> None:
        """Merge a step's stored artifacts into the shared store."""
        outputs = getattr(step.task_step, "outputs", None)
        if outputs and isinstance(outputs, dict):
            embedded = outputs.get("_artifacts")
            if isinstance(embedded, dict):
                artifacts.update(embedded)

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------

    async def _emit(self, event: str, task_id: UUID, data: dict[str, Any] | None = None) -> None:
        await self.event_bus.emit(event, str(task_id), data)

    # ------------------------------------------------------------------
    # Step attribute accessors
    # ------------------------------------------------------------------

    @staticmethod
    def _step_key(step: _StepRuntime) -> str:
        return step.task_step.step_key

    @staticmethod
    def _step_type(step: _StepRuntime) -> str:
        return step.task_step.step_type

    @staticmethod
    def _step_status(step: _StepRuntime) -> str:
        return step.task_step.status

    @staticmethod
    def _step_config(step: _StepRuntime) -> dict[str, Any]:
        config = step.task_step.config_snapshot
        if config is None:
            return {}
        if isinstance(config, dict):
            return config
        return {}

    @staticmethod
    def _step_enabled(step: _StepRuntime) -> bool:
        if step.pipeline_step is not None:
            return step.pipeline_step.enabled
        return True

    @staticmethod
    def _step_display_order(step: _StepRuntime) -> int:
        if step.pipeline_step is not None:
            return step.pipeline_step.display_order
        return 0

    @staticmethod
    def _step_depends_on(step: _StepRuntime) -> list[str]:
        if step.pipeline_step is not None:
            deps = step.pipeline_step.depends_on
            if isinstance(deps, list):
                return deps
        return []

    @staticmethod
    def _step_max_retries(step: _StepRuntime) -> int:
        if step.pipeline_step is not None:
            policy = step.pipeline_step.retry_policy
            if isinstance(policy, dict):
                return policy.get("max_retries", 0)
        return 0

    @staticmethod
    def _step_attempt(step: _StepRuntime) -> int:
        return step.task_step.attempt or 1
