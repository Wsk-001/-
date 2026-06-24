from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ArticleCreate(BaseModel):
    task_id: Optional[uuid.UUID] = None
    article_json: dict
    template_key: Optional[str] = None
    created_by: str = "llm"


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, by_alias=True)

    id: uuid.UUID
    task_id: Optional[uuid.UUID]
    version: int
    article_json: dict = Field(alias="content")
    template_key: Optional[str]
    is_current: bool
    created_by: str
    created_at: datetime


class ArticleValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
