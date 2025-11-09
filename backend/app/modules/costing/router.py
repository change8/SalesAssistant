"""API endpoints for cost estimation."""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core import dependencies
from backend.app.core.database import SessionLocal
from backend.app.modules.tasks import schemas as task_schemas
from backend.app.modules.tasks.schemas import TaskType
from backend.app.modules.tasks.service import TaskService

from .schemas import CostingRequest
from .service import CostEstimator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["costing"])

_service = CostEstimator()


def _parse_config(payload: Optional[str]) -> CostingRequest:
    if payload is None or payload.strip() == "":
        return CostingRequest()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="配置字段需为合法 JSON") from exc
    return CostingRequest.model_validate(data)


def _serialize_task(task) -> task_schemas.TaskDetail:
    return task_schemas.TaskDetail.model_validate(task)


def _run_costing_task(
    task_id: int,
    filename: str,
    file_bytes: bytes,
    config_payload: dict,
) -> None:
    db = SessionLocal()
    task_service = TaskService(db)
    try:
        task_service.mark_running(task_id)
        response = _service.estimate(
            file_bytes=file_bytes,
            filename=filename,
            config=CostingRequest(config=config_payload).config,
        )
        task_service.mark_succeeded(
            task_id,
            result_payload=response.model_dump(),
            description=f"成本预估 · {filename}",
        )
    except Exception as exc:  # pragma: no cover - runtime safeguard
        logger.exception(
            f"Costing task {task_id} failed for file '{filename}'",
            extra={"task_id": task_id, "filename": filename},
        )
        task_service.mark_failed(task_id, str(exc))
    finally:
        db.close()


@router.post("/analyze", response_model=task_schemas.TaskDetail)
async def analyze_cost(
    background_tasks: BackgroundTasks,
    current_user=Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
    file: UploadFile = File(..., description="功能清单 Excel"),
    config: Optional[str] = Form(None, description="JSON 配置（费率/系数）"),
):
    request_model = _parse_config(config)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    filename = file.filename or "uploaded.xlsx"
    config_payload = request_model.config.model_dump()
    task_service = TaskService(db)
    task = task_service.create_task(
        owner_id=current_user.id,
        task_type=TaskType.COSTING,
        description=f"成本预估 · {filename}",
        request_payload={"filename": filename, "config": config_payload},
    )
    background_tasks.add_task(_run_costing_task, task.id, filename, file_bytes, config_payload)
    return _serialize_task(task)
