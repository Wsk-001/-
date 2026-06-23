from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.types import GUID, uuid_default

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="editor")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pipelines = relationship("Pipeline", back_populates="owner", foreign_keys="Pipeline.owner_id")
    tasks = relationship("Task", back_populates="owner", foreign_keys="Task.owner_id")
    prompts = relationship("Prompt", back_populates="owner", foreign_keys="Prompt.owner_id")
