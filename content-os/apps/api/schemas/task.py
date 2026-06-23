from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    pipeline_id: uuid.UUID
    title: str | None = None
    inputs: dict = {}


class TaskStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    step_key: str
    step_type: str
    status: str
    config_snapshot: dict
    inputs: dict
    outputs: dict
    attempt: int
    error: str | None
    stack_trace: str | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    owner_id: uuid.UUID
    title: str | None
    status: str
    inputs: dict
    current_step_key: str | None
    progress: int
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    steps: list[TaskStepResponse] = []
