"""Workload assistant router integrating SplitWorkload service."""

from __future__ import annotations

import io
import json
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from SplitWorkload.backend.app.models.api import AnalyzeRequest, AnalysisResponse
from SplitWorkload.backend.app.services.workload_service import WorkloadService

from backend.app.core import dependencies

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


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_workbook(
    current_user=Depends(dependencies.get_current_user),
    file: UploadFile = File(..., description="Excel 功能清单"),
    config: Optional[str] = Form(None, description="JSON 配置"),
):
    request_model = _safe_parse_config(config)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    return _service.process_workbook(
        file_bytes=file_bytes,
        filename=file.filename or "uploaded.xlsx",
        config=request_model.config,
    )


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
