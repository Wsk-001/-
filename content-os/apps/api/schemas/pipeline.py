from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PipelineStepCreate(BaseModel):
    step_key: str
    step_type: str
    name: str
    display_order: int = 0
    config: dict = {}
    prompt_id: uuid.UUID | None = None
    llm_config_id: uuid.UUID | None = None
    depends_on: list[str] = []
    enabled: bool = True
    retry_policy: dict = {}


class PipelineStepUpdate(BaseModel):
    step_key: str | None = None
    step_type: str | None = None
    name: str | None = None
    display_order: int | None = None
    config: dict | None = None
    prompt_id: uuid.UUID | None = None
    llm_config_id: uuid.UUID | None = None
    depends_on: list[str] | None = None
    enabled: bool | None = None
    retry_policy: dict | None = None


class PipelineStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    step_key: str
    step_type: str
    name: str
    display_order: int
    config: dict
    prompt_id: uuid.UUID | None
    llm_config_id: uuid.UUID | None
    depends_on: list
    enabled: bool
    retry_policy: dict


class PipelineCreate(BaseModel):
    name: str
    description: str | None = None
    template_key: str = "daily-intelligence"
    is_default: bool = False
    steps: list[PipelineStepCreate] = []


class PipelineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    template_key: str | None = None
    is_default: bool | None = None


class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    template_key: str
    is_default: bool
    version: int
    steps: list[PipelineStepResponse] = []
    created_at: datetime
    updated_at: datetime
