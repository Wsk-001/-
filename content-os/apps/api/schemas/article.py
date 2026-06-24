from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArticleCreate(BaseModel):
    task_id: uuid.UUID | None = None
    article_json: dict
    template_key: str | None = None
    created_by: str = "llm"


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, by_alias=True)

    id: uuid.UUID
    task_id: uuid.UUID | None
    version: int
    article_json: dict = Field(alias="content")
    template_key: str | None
    is_current: bool
    created_by: str
    created_at: datetime


class ArticleValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
