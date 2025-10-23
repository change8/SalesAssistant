"""Workload assistant router integrating SplitWorkload service."""

from __future__ import annotations

import io
import json
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from SplitWorkload.backend.app.models.api import AnalyzeRequest, ConstraintConfig
from SplitWorkload.backend.app.services.workload_service import WorkloadService

from backend.app.core import dependencies
from backend.app.core.database import SessionLocal
from backend.app.modules.tasks import schemas as task_schemas
from backend.app.modules.tasks.schemas import TaskType
from backend.app.modules.tasks.service import TaskService

router = APIRouter(tags=["workload"])

_service = WorkloadService()


def _safe_parse_config(payload: Optional[str]) -> AnalyzeRequest:
    if payload is None or payload.strip() == "":
        return AnalyzeRequest()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="配置字段需为合法 JSON") from exc
    return AnalyzeRequest.model_validate(data)


def _ascii_fallback(name: str) -> str:
    return "".join(ch if ch.isascii() else "_" for ch in name) or "splitworkload_analysis.xlsx"


def _build_export_filename(original: Optional[str]) -> str:
    if not original:
        return "splitworkload_analysis.xlsx"
    stem = original.rsplit(".", 1)[0] or "analysis"
    return f"{stem}_analysis.xlsx"


def _serialize_task(task) -> task_schemas.TaskDetail:
    return task_schemas.TaskDetail.model_validate(task)


def _run_workload_task(
    task_id: int,
    filename: str,
    file_bytes: bytes,
    config_payload: dict,
) -> None:
    db = SessionLocal()
    service = TaskService(db)
    try:
        service.mark_running(task_id)
        response = _service.process_workbook(
            file_bytes=file_bytes,
            filename=filename,
            config=ConstraintConfig(**config_payload),
        )
        service.mark_succeeded(
            task_id,
            result_payload=response.model_dump(),
            description=f"工时拆分 · {filename}",
        )
    except Exception as exc:  # pragma: no cover - runtime safeguard
        service.mark_failed(task_id, str(exc))
    finally:
        db.close()


@router.post("/analyze", response_model=task_schemas.TaskDetail)
async def analyze_workbook(
    background_tasks: BackgroundTasks,
    current_user=Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
    file: UploadFile = File(..., description="Excel 功能清单"),
    config: Optional[str] = Form(None, description="JSON 配置"),
):
    request_model = _safe_parse_config(config)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    filename = file.filename or "uploaded.xlsx"
    config_payload = request_model.config.model_dump()
    task_service = TaskService(db)
    task = task_service.create_task(
        owner_id=current_user.id,
        task_type=TaskType.WORKLOAD,
        description=f"工时拆分 · {filename}",
        request_payload={"filename": filename, "config": config_payload},
    )
    background_tasks.add_task(_run_workload_task, task.id, filename, file_bytes, config_payload)
    return _serialize_task(task)


@router.post("/export")
async def export_workbook(
    current_user=Depends(dependencies.get_current_user),
    file: UploadFile = File(..., description="Excel 功能清单"),
    config: Optional[str] = Form(None, description="JSON 配置"),
):
    request_model = _safe_parse_config(config)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    response, workbook_bytes = _service.export_workbook(
        file_bytes=file_bytes,
        filename=file.filename or "uploaded.xlsx",
        config=request_model.config,
    )

    download_name = _build_export_filename(file.filename)
    headers = {
        "Content-Disposition": (
            f"attachment; filename=\"{_ascii_fallback(download_name)}\"; filename*=UTF-8''{quote(download_name)}"
        )
    }

    return StreamingResponse(
        content=io.BytesIO(workbook_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
