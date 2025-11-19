"""API routes for task management."""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.auth.models import User
from backend.app.core.dependencies import get_current_user, get_db
from backend.app.tasks.models import Task, TaskStatus, TaskType
from backend.app.tasks.service import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ============================= Schemas =============================


class TaskCreateRequest(BaseModel):
    """Request to create a new task."""

    task_type: TaskType
    payload: Dict[str, Any]
    max_retries: int = Field(default=3, ge=0, le=10)


class TaskResponse(BaseModel):
    """Task response model."""

    id: int
    task_type: TaskType
    status: TaskStatus
    retry_count: int
    max_retries: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class TaskWithResultResponse(TaskResponse):
    """Task response with result data."""

    result: Optional[Dict[str, Any]] = None


class TaskListResponse(BaseModel):
    """List of tasks."""

    tasks: List[TaskResponse]
    total: int


class TaskStatsResponse(BaseModel):
    """Task statistics."""

    stats: Dict[str, int]


# ============================= Endpoints =============================


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    request: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Create a new async task.

    The task will be queued and processed by a background worker.
    """
    task_service = TaskService(db)

    task = task_service.create_task(
        task_type=request.task_type,
        user_id=current_user.id,
        payload=request.payload,
        max_retries=request.max_retries,
    )

    logger.info(
        f"Created task {task.id} for user {current_user.id}",
        extra={"task_id": task.id, "user_id": current_user.id, "task_type": request.task_type},
    )

    return task


@router.post("/bidding/text", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_bidding_text_task(
    text: str = Form(...),
    max_retries: int = Form(default=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Create a bidding analysis task from text input."""
    task_service = TaskService(db)

    payload = {"text": text}

    task = task_service.create_task(
        task_type=TaskType.BIDDING_ANALYSIS,
        user_id=current_user.id,
        payload=payload,
        max_retries=max_retries,
        metadata={"source": "text"},
    )

    logger.info(f"Created bidding text analysis task {task.id} for user {current_user.id}")
    return task


@router.post("/bidding/file", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_bidding_file_task(
    file: UploadFile = File(...),
    max_retries: int = Form(default=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Create a bidding analysis task from file upload."""
    task_service = TaskService(db)

    # Read and encode file
    file_bytes = await file.read()
    file_base64 = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "file_base64": file_base64,
        "filename": file.filename,
        "content_type": file.content_type,
    }

    task = task_service.create_task(
        task_type=TaskType.BIDDING_ANALYSIS,
        user_id=current_user.id,
        payload=payload,
        max_retries=max_retries,
        metadata={"source": "file", "filename": file.filename},
    )

    logger.info(
        f"Created bidding file analysis task {task.id} for user {current_user.id} (file={file.filename})"
    )
    return task


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    task_type: Optional[TaskType] = None,
    status_filter: Optional[TaskStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    """List tasks for the current user with optional filters."""
    task_service = TaskService(db)

    tasks = task_service.list_tasks(
        user_id=current_user.id,
        task_type=task_type,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.get("/stats", response_model=TaskStatsResponse)
def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskStatsResponse:
    """Get task statistics for the current user."""
    task_service = TaskService(db)
    stats = task_service.get_task_stats(user_id=current_user.id)
    return TaskStatsResponse(stats=stats)


@router.get("/{task_id}", response_model=TaskWithResultResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    """Get task details by ID.

    Only returns tasks owned by the current user.
    """
    task_service = TaskService(db)

    task = task_service.get_task(task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    return task


@router.delete("/{task_id}")
def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Cancel a pending or running task.

    Only the task owner can cancel the task.
    """
    task_service = TaskService(db)

    task = task_service.cancel_task(task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found or cannot be cancelled",
        )

    logger.info(f"Cancelled task {task_id} by user {current_user.id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
