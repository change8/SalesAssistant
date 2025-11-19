"""Business logic helpers for task management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence

from fastapi.encoders import jsonable_encoder
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from . import schemas
from .models import TaskOld as Task


class TaskNotFoundError(RuntimeError):
    """Raised when the requested task cannot be found or accessed."""


class TaskService:
    """Encapsulate task CRUD operations with convenience helpers."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------ create/update
    def create_task(
        self,
        *,
        owner_id: int,
        task_type: schemas.TaskType | str,
        description: Optional[str] = None,
        request_payload: Optional[Any] = None,
    ) -> Task:
        task = Task(
            owner_id=owner_id,
            task_type=self._normalize_type(task_type),
            status=schemas.TaskStatus.PENDING.value,
            description=description,
            request_payload=self._encode(request_payload),
        )
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def mark_running(self, task_id: int) -> Task:
        task = self._get(task_id)
        task.status = schemas.TaskStatus.RUNNING.value
        task.started_at = datetime.now(tz=timezone.utc)
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def mark_succeeded(self, task_id: int, result_payload: Optional[Any] = None, *, description: Optional[str] = None) -> Task:
        task = self._get(task_id)
        task.status = schemas.TaskStatus.SUCCEEDED.value
        task.finished_at = datetime.now(tz=timezone.utc)
        if result_payload is not None:
            task.result_payload = self._encode(result_payload)
        if description is not None:
            task.description = description
        task.error_message = None
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def mark_failed(self, task_id: int, error_message: str, *, result_payload: Optional[Any] = None) -> Task:
        task = self._get(task_id)
        task.status = schemas.TaskStatus.FAILED.value
        task.finished_at = datetime.now(tz=timezone.utc)
        task.error_message = (error_message or "")[:1000]
        if result_payload is not None:
            task.result_payload = self._encode(result_payload)
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    # ------------------------------------------------------------------ read
    def list_tasks(
        self,
        *,
        owner_id: int,
        limit: int = 20,
        status: Optional[schemas.TaskStatus | str] = None,
        task_type: Optional[schemas.TaskType | str] = None,
        include_history: bool = False,
    ) -> List[Task]:
        stmt = self._base_query(owner_id=owner_id)
        if task_type:
            stmt = stmt.where(Task.task_type == self._normalize_type(task_type))
        if status:
            stmt = stmt.where(Task.status == self._normalize_status(status))
        else:
            if include_history:
                stmt = stmt.where(
                    Task.status.in_(
                        [
                            schemas.TaskStatus.SUCCEEDED.value,
                            schemas.TaskStatus.FAILED.value,
                        ]
                    )
                )
            else:
                active: Sequence[str] = [
                    schemas.TaskStatus.PENDING.value,
                    schemas.TaskStatus.RUNNING.value,
                ]
                stmt = stmt.where(Task.status.in_(active))
        stmt = stmt.order_by(Task.created_at.desc()).limit(limit)
        return list(self._db.scalars(stmt))

    def get_task(self, *, owner_id: int, task_id: int) -> Task:
        task = self._get(task_id)
        if task.owner_id != owner_id:
            raise TaskNotFoundError("任务不存在或无权访问")
        return task

    # ------------------------------------------------------------------ internal
    def _base_query(self, *, owner_id: int) -> Select[Task]:
        return select(Task).where(Task.owner_id == owner_id)

    def _get(self, task_id: int) -> Task:
        task = self._db.get(Task, task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return task

    @staticmethod
    def _encode(payload: Optional[Any]) -> Optional[Any]:
        if payload is None:
            return None
        return jsonable_encoder(payload)

    @staticmethod
    def _normalize_type(task_type: schemas.TaskType | str) -> str:
        if isinstance(task_type, schemas.TaskType):
            return task_type.value
        return str(task_type)

    @staticmethod
    def _normalize_status(status: schemas.TaskStatus | str) -> str:
        if isinstance(status, schemas.TaskStatus):
            return status.value
        return str(status)
