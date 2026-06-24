from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LLMConfigCreate(BaseModel):
    name: str
    provider: str
    model: str
    api_key_encrypted: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    is_default: bool = False


class LLMConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    provider: str
    model: str
    api_key_encrypted: Optional[str]
    base_url: Optional[str]
    temperature: float
    max_tokens: int
    is_default: bool
    created_at: datetime
