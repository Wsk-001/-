from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PromptVersionCreate(BaseModel):
    content: str
    variables_schema: list = []
    output_schema: dict = {}
    model_hint: Optional[str] = None
    changelog: Optional[str] = None


class PromptVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prompt_id: uuid.UUID
    version: int
    content: str
    variables_schema: list
    output_schema: dict
    model_hint: Optional[str]
    changelog: Optional[str]
    created_at: datetime


class PromptCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    initial_version: Optional[PromptVersionCreate] = None


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, by_alias=True)

    id: uuid.UUID
    owner_id: Optional[uuid.UUID]
    name: str
    description: Optional[str]
    category: str
    current_version_id: Optional[uuid.UUID]
    created_at: datetime
    current_version: Optional[PromptVersionResponse] = None


class PromptDryRunRequest(BaseModel):
    variables: dict = {}
    model_hint: Optional[str] = None
