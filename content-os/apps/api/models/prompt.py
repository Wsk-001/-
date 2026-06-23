from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.types import GUID, JSONDict, uuid_default

from core.database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Text | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("prompt_versions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="prompts", foreign_keys=[owner_id])
    current_version = relationship("PromptVersion", foreign_keys=[current_version_id], post_update=True)
    versions = relationship("PromptVersion", back_populates="prompt", foreign_keys="PromptVersion.prompt_id", cascade="all, delete-orphan")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    prompt_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema: Mapped[list] = mapped_column(JSONDict, default=list)
    output_schema: Mapped[dict] = mapped_column(JSONDict, default=dict)
    model_hint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    changelog: Mapped[Text | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prompt = relationship("Prompt", back_populates="versions", foreign_keys=[prompt_id])
