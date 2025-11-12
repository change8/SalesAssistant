"""Task models for persistent async job management."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.common.models import TimestampMixin
from backend.app.core.database import Base


class TaskStatus(str, enum.Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"  # Waiting for retry
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    """Type of task to execute."""

    BIDDING_ANALYSIS = "bidding_analysis"
    WORKLOAD_ANALYSIS = "workload_analysis"
    COST_ESTIMATION = "cost_estimation"


class Task(TimestampMixin, Base):
    """Persistent task record for async LLM operations.

    This model stores all task metadata, execution state, and results.
    A background worker polls pending tasks and executes them.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Task identification
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True,
    )

    # Ownership
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped["User"] = relationship("User", back_populates="tasks")  # type: ignore

    # Task payload (input data)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Execution metadata
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Results
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata for debugging and monitoring
    task_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status}, user_id={self.user_id})>"

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state (no further processing needed)."""
        return self.status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries and self.status in {TaskStatus.FAILED, TaskStatus.RETRY}

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
