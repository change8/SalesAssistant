"""Pydantic schemas for task APIs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TaskType(str, Enum):
    BIDDING = "bidding_analysis"
    WORKLOAD = "workload_analysis"
    COSTING = "costing_estimate"

    def label(self) -> str:
        mapping = {
            TaskType.BIDDING: "标书分析",
            TaskType.WORKLOAD: "工时拆分",
            TaskType.COSTING: "成本预估",
        }
        return mapping.get(self, self.value)


class TaskSummary(BaseModel):
    id: int
    task_type: TaskType
    status: TaskStatus
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class TaskDetail(TaskSummary):
    request_payload: Optional[Dict[str, Any]] = None
    result_payload: Optional[Dict[str, Any]] = None


class TaskListResponse(BaseModel):
    items: List[TaskSummary]


class TaskHistoryResponse(BaseModel):
    items: List[TaskSummary]
