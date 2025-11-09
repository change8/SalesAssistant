"""Utilities to sync bidding jobs with the unified task tracker."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from BiddingAssistant.backend.storage.memory import AnalysisJobRecord

from backend.app.core.database import SessionLocal
from backend.app.modules.tasks.service import TaskNotFoundError, TaskService

logger = logging.getLogger(__name__)


def build_task_observer():
    """Return a callback that mirrors bidding job progress to the TaskService."""

    def observer(job: AnalysisJobRecord) -> None:
        metadata: Dict[str, Any] = job.metadata or {}
        task_id_raw: Optional[Any] = metadata.get("task_id")
        if task_id_raw is None:
            return
        try:
            task_id = int(task_id_raw)
        except (TypeError, ValueError):
            logger.warning("Unexpected task_id on bidding job %s: %s", job.job_id, task_id_raw)
            return

        db = SessionLocal()
        service = TaskService(db)
        try:
            if job.status == "processing":
                service.mark_running(task_id)
            elif job.status == "completed":
                payload = {
                    "job_id": job.job_id,
                    "metadata": metadata,
                    "result": job.result,
                }
                filename = metadata.get("filename") or job.filename or "标书"
                service.mark_succeeded(task_id, result_payload=payload, description=f"标书分析 · {filename}")
            elif job.status == "failed":
                payload = {
                    "job_id": job.job_id,
                    "metadata": metadata,
                    "error": job.error,
                }
                error_message = job.error or "分析失败"
                service.mark_failed(task_id, error_message, result_payload=payload)
        except TaskNotFoundError:
            logger.warning("Task %s missing when syncing bidding job %s", task_id, job.job_id)
        except Exception:
            logger.exception("Failed syncing bidding job %s to task %s", job.job_id, task_id)
        finally:
            db.close()

    return observer
