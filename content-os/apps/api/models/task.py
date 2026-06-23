from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.types import GUID, JSONDict, uuid_default

from core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    pipeline_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("pipelines.id"), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    inputs: Mapped[dict] = mapped_column(JSONDict, default=dict)
    current_step_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Text | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pipeline = relationship("Pipeline", back_populates="tasks")
    owner = relationship("User", back_populates="tasks", foreign_keys=[owner_id])
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan", order_by="TaskStep.step_key")
    articles = relationship("Article", back_populates="task")
    source_bundles = relationship("SourceBundle", back_populates="task")
    execution_logs = relationship("ExecutionLog", back_populates="task")
    wechat_publications = relationship("WechatPublication", back_populates="task")


class TaskStep(Base):
    __tablename__ = "task_steps"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid_default)
    task_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    step_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    config_snapshot: Mapped[dict] = mapped_column(JSONDict, default=dict)
    inputs: Mapped[dict] = mapped_column(JSONDict, default=dict)
    outputs: Mapped[dict] = mapped_column(JSONDict, default=dict)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    error: Mapped[Text | None] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[Text | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    task = relationship("Task", back_populates="steps")
