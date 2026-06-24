from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Optional

from models.types import GUID, JSONDict, uuid_default

from core.database import Base


class SourceBundle(Base):
    __tablename__ = "source_bundles"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("tasks.id"), nullable=True)
    spec: Mapped[dict] = mapped_column(JSONDict, default=dict)
    bundle: Mapped[dict] = mapped_column(JSONDict, default=dict)
    storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="source_bundles")
