"""Background worker for processing database-backed async tasks."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.tasks.models import Task, TaskStatus, TaskType
from backend.app.tasks.service import TaskService
from backend.app.tasks.executors import (
    BiddingAnalysisExecutor,
    WorkloadAnalysisExecutor,
    CostEstimationExecutor,
)

logger = logging.getLogger(__name__)


class TaskWorker:
    """Background worker that polls database for pending tasks and executes them.

    This worker runs in a separate process/thread and continuously:
    1. Polls database for pending/retry tasks
    2. Executes tasks using appropriate executors
    3. Updates task status and results
    4. Handles retries on failure
    5. Gracefully shuts down on signals
    """

    def __init__(
        self,
        poll_interval: float = 2.0,
        batch_size: int = 5,
        max_consecutive_errors: int = 10,
    ) -> None:
        """Initialize worker.

        Args:
            poll_interval: Seconds to wait between polling cycles
            batch_size: Maximum number of tasks to process per cycle
            max_consecutive_errors: Stop worker after this many consecutive errors
        """
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.max_consecutive_errors = max_consecutive_errors

        self._running = False
        self._consecutive_errors = 0

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down gracefully...")
        self._running = False

    def start(self) -> None:
        """Start the worker loop.

        This method blocks until the worker is stopped via signal or error.
        """
        logger.info(
            f"Starting task worker (poll_interval={self.poll_interval}s, batch_size={self.batch_size})"
        )
        self._running = True
        self._consecutive_errors = 0

        while self._running:
            try:
                processed = self._process_batch()

                # Reset error counter on successful batch
                if processed >= 0:
                    self._consecutive_errors = 0

                # Sleep before next poll
                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                logger.info("Worker interrupted by user")
                break

            except Exception as exc:
                self._consecutive_errors += 1
                logger.error(
                    f"Worker batch error ({self._consecutive_errors}/{self.max_consecutive_errors}): {exc}",
                    exc_info=True,
                )

                if self._consecutive_errors >= self.max_consecutive_errors:
                    logger.critical("Max consecutive errors reached, stopping worker")
                    break

                # Back off on errors
                time.sleep(min(self.poll_interval * 2, 10.0))

        logger.info("Task worker stopped")

    def _process_batch(self) -> int:
        """Process one batch of pending tasks.

        Returns:
            Number of tasks processed (can be 0)
        """
        db = SessionLocal()
        try:
            task_service = TaskService(db)

            # Get pending tasks
            tasks = task_service.get_pending_tasks(limit=self.batch_size)

            if not tasks:
                logger.debug("No pending tasks found")
                return 0

            logger.info(f"Processing batch of {len(tasks)} tasks")

            for task in tasks:
                try:
                    self._process_task(task, task_service)
                except Exception as exc:
                    logger.error(
                        f"Failed to process task {task.id}: {exc}",
                        exc_info=True,
                        extra={"task_id": task.id, "task_type": task.task_type},
                    )
                    # Individual task errors don't count as worker errors
                    pass

            return len(tasks)

        finally:
            db.close()

    def _process_task(self, task: Task, task_service: TaskService) -> None:
        """Process a single task.

        Args:
            task: Task to process
            task_service: TaskService instance for updates
        """
        task_id = task.id
        task_type = task.task_type

        logger.info(
            f"Processing task {task_id} (type={task_type}, retry={task.retry_count})",
            extra={"task_id": task_id, "task_type": task_type, "retry_count": task.retry_count},
        )

        # Update status to RUNNING
        task_service.update_task_status(task_id, TaskStatus.RUNNING)

        start_time = time.time()

        try:
            # Execute task based on type
            result = self._execute_task(task)

            duration_ms = (time.time() - start_time) * 1000

            # Update status to COMPLETED
            task_service.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result=result,
                metadata_update={
                    "duration_ms": round(duration_ms, 2),
                    "completed_at_timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(
                f"Task {task_id} completed successfully ({duration_ms:.0f}ms)",
                extra={
                    "task_id": task_id,
                    "task_type": task_type,
                    "duration_ms": duration_ms,
                },
            )

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(exc)

            logger.error(
                f"Task {task_id} failed: {error_msg}",
                exc_info=True,
                extra={
                    "task_id": task_id,
                    "task_type": task_type,
                    "error": error_msg,
                    "duration_ms": duration_ms,
                },
            )

            # Determine if task should retry
            if task.can_retry:
                logger.info(f"Task {task_id} will retry (attempt {task.retry_count + 1}/{task.max_retries})")
                task_service.increment_retry(task_id)
            else:
                # Mark as FAILED
                task_service.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    error=error_msg,
                    metadata_update={
                        "duration_ms": round(duration_ms, 2),
                        "failed_at_timestamp": datetime.utcnow().isoformat(),
                        "retry_exhausted": True,
                    },
                )

    def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute task based on type.

        Args:
            task: Task to execute

        Returns:
            Task result dictionary

        Raises:
            Exception: If task execution fails
        """
        if task.task_type == TaskType.BIDDING_ANALYSIS:
            executor = BiddingAnalysisExecutor()
            return executor.execute(task.payload)

        elif task.task_type == TaskType.WORKLOAD_ANALYSIS:
            executor = WorkloadAnalysisExecutor()
            return executor.execute(task.payload)

        elif task.task_type == TaskType.COST_ESTIMATION:
            executor = CostEstimationExecutor()
            return executor.execute(task.payload)

        else:
            raise ValueError(f"Unknown task type: {task.task_type}")


def run_worker() -> None:
    """Entry point for running the worker as a standalone process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("Initializing task worker...")

    worker = TaskWorker(
        poll_interval=2.0,
        batch_size=5,
        max_consecutive_errors=10,
    )

    try:
        worker.start()
    except Exception as exc:
        logger.critical(f"Worker crashed: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_worker()
