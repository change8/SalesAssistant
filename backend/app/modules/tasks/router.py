"""REST endpoints for unified task management."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core import dependencies

from . import schemas, service

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _serialize_summary(task) -> schemas.TaskSummary:
    return schemas.TaskSummary.model_validate(task)


def _serialize_detail(task) -> schemas.TaskDetail:
    return schemas.TaskDetail.model_validate(task)


@router.get("", response_model=schemas.TaskListResponse)
def list_active_tasks(
    limit: int = Query(20, ge=1, le=100),
    task_type: Optional[schemas.TaskType] = Query(None, description="筛选任务类型"),
    status_filter: Optional[schemas.TaskStatus] = Query(None, description="筛选任务状态"),
    current_user=Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    task_service = service.TaskService(db)
    tasks = task_service.list_tasks(
        owner_id=current_user.id,
        limit=limit,
        task_type=task_type,
        status=status_filter,
        include_history=False,
    )
    return schemas.TaskListResponse(items=[_serialize_summary(task) for task in tasks])


@router.get("/history", response_model=schemas.TaskHistoryResponse)
def list_history_tasks(
    limit: int = Query(50, ge=1, le=200),
    task_type: Optional[schemas.TaskType] = Query(None, description="筛选任务类型"),
    current_user=Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    task_service = service.TaskService(db)
    tasks = task_service.list_tasks(
        owner_id=current_user.id,
        limit=limit,
        task_type=task_type,
        include_history=True,
    )
    return schemas.TaskHistoryResponse(items=[_serialize_summary(task) for task in tasks])


@router.get("/{task_id}", response_model=schemas.TaskDetail)
def get_task_detail(
    task_id: int,
    current_user=Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    task_service = service.TaskService(db)
    try:
        task = task_service.get_task(owner_id=current_user.id, task_id=task_id)
    except service.TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _serialize_detail(task)
