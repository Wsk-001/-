from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceCollectRequest(BaseModel):
    spec: dict = {}
    task_id: uuid.UUID | None = None


class SourceBundleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID | None
    spec: dict
    bundle: dict
    storage_key: str | None
    created_at: datetime
