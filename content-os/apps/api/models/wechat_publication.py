from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.types import GUID, uuid_default

from core.database import Base


class WechatPublication(Base):
    __tablename__ = "wechat_publications"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    task_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tasks.id"), nullable=False)
    draft_media_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publish_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    article_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft_created")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="wechat_publications")
