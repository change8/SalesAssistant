"""Task service for managing persistent async jobs."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.tasks.models import Task, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class TaskService:
    """Service layer for task CRUD operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(
        self,
        *,
        task_type: TaskType,
        user_id: int,
        payload: Dict[str, Any],
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Create a new task in PENDING status.

        Args:
            task_type: Type of task to execute
            user_id: ID of the user who owns this task
            payload: Input data for the task
            max_retries: Maximum number of retry attempts
            metadata: Optional metadata for debugging

        Returns:
            Created task instance
        """
        task = Task(
            task_type=task_type,
            user_id=user_id,
            payload=payload,
            status=TaskStatus.PENDING,
            max_retries=max_retries,
            task_metadata=metadata or {},
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        logger.info(
            f"Created task {task.id} (type={task_type}, user_id={user_id})",
            extra={"task_id": task.id, "task_type": task_type, "user_id": user_id},
        )
        return task

    def get_task(self, task_id: int, user_id: Optional[int] = None) -> Optional[Task]:
        """Retrieve a task by ID, optionally filtered by user.

        Args:
            task_id: Task ID
            user_id: If provided, only return task if it belongs to this user

        Returns:
            Task instance or None if not found
        """
        stmt = select(Task).where(Task.id == task_id)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def list_tasks(
        self,
        *,
        user_id: Optional[int] = None,
        task_type: Optional[TaskType] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Task]:
        """List tasks with optional filters.

        Args:
            user_id: Filter by user ID
            task_type: Filter by task type
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of tasks sorted by created_at DESC
        """
        stmt = select(Task).order_by(Task.created_at.desc())

        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)
        if task_type is not None:
            stmt = stmt.where(Task.task_type == task_type)
        if status is not None:
            stmt = stmt.where(Task.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        *,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        metadata_update: Optional[Dict[str, Any]] = None,
    ) -> Optional[Task]:
        """Update task status and associated fields.

        Args:
            task_id: Task ID
            status: New status
            error: Error message if status is FAILED
            result: Result data if status is COMPLETED
            metadata_update: Additional metadata to merge

        Returns:
            Updated task or None if not found
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for status update")
            return None

        task.status = status

        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.utcnow()

        if status in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
            task.completed_at = datetime.utcnow()

        if error is not None:
            task.error = error

        if result is not None:
            task.result = result

        if metadata_update:
            merged_metadata = task.task_metadata.copy()
            merged_metadata.update(metadata_update)
            task.task_metadata = merged_metadata

        self.db.commit()
        self.db.refresh(task)

        logger.info(
            f"Updated task {task_id} status to {status}",
            extra={
                "task_id": task_id,
                "status": status,
                "has_error": bool(error),
                "has_result": bool(result),
            },
        )
        return task

    def increment_retry(self, task_id: int) -> Optional[Task]:
        """Increment retry count and set status to RETRY if possible.

        Args:
            task_id: Task ID

        Returns:
            Updated task or None if retry not allowed
        """
        task = self.get_task(task_id)
        if not task:
            return None

        if not task.can_retry:
            logger.warning(
                f"Task {task_id} cannot retry (count={task.retry_count}, max={task.max_retries})"
            )
            return None

        task.retry_count += 1
        task.status = TaskStatus.RETRY
        task.error = None  # Clear previous error
        self.db.commit()
        self.db.refresh(task)

        logger.info(
            f"Incremented retry for task {task_id} (attempt {task.retry_count}/{task.max_retries})",
            extra={"task_id": task_id, "retry_count": task.retry_count},
        )
        return task

    def cancel_task(self, task_id: int, user_id: Optional[int] = None) -> Optional[Task]:
        """Cancel a pending or running task.

        Args:
            task_id: Task ID
            user_id: If provided, only cancel if task belongs to this user

        Returns:
            Cancelled task or None if not found/not cancellable
        """
        task = self.get_task(task_id, user_id=user_id)
        if not task or task.is_terminal:
            return None

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)

        logger.info(f"Cancelled task {task_id}", extra={"task_id": task_id})
        return task

    def get_pending_tasks(self, limit: int = 10) -> List[Task]:
        """Get pending or retry tasks for worker processing.

        Args:
            limit: Maximum number of tasks to fetch

        Returns:
            List of tasks ready for execution
        """
        stmt = (
            select(Task)
            .where(Task.status.in_([TaskStatus.PENDING, TaskStatus.RETRY]))
            .order_by(Task.created_at.asc())
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_task_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get task statistics.

        Args:
            user_id: If provided, filter stats by user

        Returns:
            Dictionary with task counts by status
        """
        from sqlalchemy import func

        stmt = select(Task.status, func.count(Task.id)).group_by(Task.status)
        if user_id is not None:
            stmt = stmt.where(Task.user_id == user_id)

        result = self.db.execute(stmt)
        stats = {status.value: count for status, count in result.all()}

        # Ensure all statuses are present
        for status in TaskStatus:
            if status.value not in stats:
                stats[status.value] = 0

        return stats
