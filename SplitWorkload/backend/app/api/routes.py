from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from SplitWorkload.backend.app.models.api import AnalyzeRequest, AnalysisResponse
from SplitWorkload.backend.app.services.workload_service import WorkloadService

router = APIRouter()
service = WorkloadService()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple health probe for uptime monitoring."""
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_workbook(
    file: UploadFile = File(..., description="Excel workbook with requirement data"),
    config: Optional[str] = Form(default=None, description="JSON configuration payload"),
) -> AnalysisResponse:
    request_model = _safe_parse_config(config)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    return service.process_workbook(
        file_bytes=file_bytes,
        filename=file.filename or "uploaded.xlsx",
        config=request_model.config,
    )


@router.post("/export")
async def export_workbook(
    file: UploadFile = File(..., description="Excel workbook with requirement data"),
    config: Optional[str] = Form(default=None, description="JSON configuration payload"),
) -> StreamingResponse:
    request_model = _safe_parse_config(config)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    _, workbook_bytes = service.export_workbook(
        file_bytes=file_bytes,
        filename=file.filename or "uploaded.xlsx",
        config=request_model.config,
    )

    download_name = _build_export_filename(file.filename)
    ascii_name = _ascii_fallback(download_name)

    headers = {
        "Content-Disposition": (
            f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(download_name)}"
        )
    }

    return StreamingResponse(
        content=io.BytesIO(workbook_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


def _safe_parse_config(payload: Optional[str]) -> AnalyzeRequest:
    if payload is None or payload.strip() == "":
        return AnalyzeRequest()

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON passed in config field") from exc

    return AnalyzeRequest.model_validate(data)


def _build_export_filename(original: Optional[str]) -> str:
    if not original:
        return "splitworkload_analysis.xlsx"
    stem = Path(original).stem or "analysis"
    return f"{stem}_analysis.xlsx"


def _ascii_fallback(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return sanitized or "splitworkload_analysis.xlsx"
