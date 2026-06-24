from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SourceCollectRequest(BaseModel):
    spec: dict = {}
    task_id: Optional[uuid.UUID] = None


class SourceBundleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: Optional[uuid.UUID]
    spec: dict
    bundle: dict
    storage_key: Optional[str]
    created_at: datetime
