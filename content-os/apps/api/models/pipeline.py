from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.types import GUID, JSONDict, uuid_default

from core.database import Base


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Text | None] = mapped_column(Text, nullable=True)
    template_key: Mapped[str] = mapped_column(String(100), default="daily-intelligence")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="pipelines", foreign_keys=[owner_id])
    steps = relationship("PipelineStep", back_populates="pipeline", cascade="all, delete-orphan", order_by="PipelineStep.display_order")
    tasks = relationship("Task", back_populates="pipeline")


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False)
    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    step_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict] = mapped_column(JSONDict, default=dict)
    prompt_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("prompts.id"), nullable=True)
    llm_config_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("llm_configs.id"), nullable=True)
    depends_on: Mapped[list] = mapped_column(JSONDict, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    retry_policy: Mapped[dict] = mapped_column(JSONDict, default=dict)

    pipeline = relationship("Pipeline", back_populates="steps")
    prompt = relationship("Prompt", foreign_keys=[prompt_id])
    llm_config = relationship("LLMConfig", foreign_keys=[llm_config_id])
