from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PipelineStepCreate(BaseModel):
    step_key: str
    step_type: str
    name: str
    display_order: int = 0
    config: dict = {}
    prompt_id: Optional[uuid.UUID] = None
    llm_config_id: Optional[uuid.UUID] = None
    depends_on: list[str] = []
    enabled: bool = True
    retry_policy: dict = {}


class PipelineStepUpdate(BaseModel):
    step_key: Optional[str] = None
    step_type: Optional[str] = None
    name: Optional[str] = None
    display_order: Optional[int] = None
    config: Optional[dict] = None
    prompt_id: Optional[uuid.UUID] = None
    llm_config_id: Optional[uuid.UUID] = None
    depends_on: Optional[list[str]] = None
    enabled: Optional[bool] = None
    retry_policy: Optional[dict] = None


class PipelineStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    step_key: str
    step_type: str
    name: str
    display_order: int
    config: dict
    prompt_id: Optional[uuid.UUID]
    llm_config_id: Optional[uuid.UUID]
    depends_on: list
    enabled: bool
    retry_policy: dict


class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_key: str = "daily-intelligence"
    is_default: bool = False
    steps: list[PipelineStepCreate] = []


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_key: Optional[str] = None
    is_default: Optional[bool] = None


class PipelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: Optional[str]
    template_key: str
    is_default: bool
    version: int
    steps: list[PipelineStepResponse] = []
    created_at: datetime
    updated_at: datetime
