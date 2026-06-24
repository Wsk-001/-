from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    pipeline_id: uuid.UUID
    title: Optional[str] = None
    inputs: dict = {}


class TaskStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, by_alias=True)

    id: uuid.UUID
    task_id: uuid.UUID
    step_key: str = Field(alias="key")
    step_type: str = Field(alias="type")
    status: str
    config_snapshot: dict = Field(default={}, alias="config")
    inputs: dict
    outputs: dict
    attempt: int = Field(default=0, alias="retry_count")
    error: Optional[str]
    stack_trace: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_ms: Optional[int]


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    owner_id: uuid.UUID
    title: Optional[str]
    status: str
    inputs: dict
    current_step_key: Optional[str]
    progress: int
    error: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime
    steps: List[TaskStepResponse] = []
