from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PromptVersionCreate(BaseModel):
    content: str
    variables_schema: list = []
    output_schema: dict = {}
    model_hint: str | None = None
    changelog: str | None = None


class PromptVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt_id: uuid.UUID
    version: int
    content: str
    variables_schema: list
    output_schema: dict
    model_hint: str | None
    changelog: str | None
    created_at: datetime


class PromptCreate(BaseModel):
    name: str
    description: str | None = None
    category: str
    initial_version: PromptVersionCreate | None = None


class PromptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID | None
    name: str
    description: str | None
    category: str
    current_version_id: uuid.UUID | None
    created_at: datetime
    current_version: PromptVersionResponse | None = None


class PromptDryRunRequest(BaseModel):
    variables: dict = {}
    model_hint: str | None = None
