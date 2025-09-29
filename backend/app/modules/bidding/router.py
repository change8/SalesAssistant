"""Unified bidding assistant API router."""

from __future__ import annotations

import io
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile

from BiddingAssistant.backend.analyzer.framework import DEFAULT_FRAMEWORK
from BiddingAssistant.backend.analyzer.llm import LLMClient
from BiddingAssistant.backend.analyzer.tender_llm import TenderLLMAnalyzer
from BiddingAssistant.backend.config import load_config
from BiddingAssistant.backend.models import AnalyzeRequest
from BiddingAssistant.backend.services.analyzer_service import AnalysisService, background_runner

from backend.app.core import dependencies

router = APIRouter(tags=["bidding"])

_config = load_config()
_llm_client = LLMClient(**_config.llm.as_kwargs())
_analyzer = TenderLLMAnalyzer(_llm_client, categories=DEFAULT_FRAMEWORK)
_service = AnalysisService(_analyzer)


def _clean_payload(payload: dict) -> dict:
    payload = dict(payload)
    payload.pop("owner_id", None)
    return payload


@router.post("/analyze/text")
async def analyze_text(
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(dependencies.get_current_user),
):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text 不能为空")

    async_mode = bool(req.async_mode)
    async_runner = None
    if async_mode:
        async_runner = lambda func, *args, **kwargs: background_runner(background_tasks, func, *args, **kwargs)

    job = _service.submit_text(
        owner_id=current_user.id,
        text=text,
        filename=req.filename,
        metadata=req.metadata,
        async_runner=async_runner,
    )
    include_result = not async_mode
    payload = _service.serialize_job(job.job_id, owner_id=current_user.id, include_result=include_result)
    return _clean_payload(payload)


@router.post("/analyze/file")
async def analyze_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    async_mode: bool = Query(False),
    filename: Optional[str] = Query(None),
    current_user=Depends(dependencies.get_current_user),
):
    file_name = filename or getattr(file, "filename", None)
    content_type = getattr(file, "content_type", None)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")
    buffer = io.BytesIO(file_bytes)

    async_runner = None
    if async_mode:
        async_runner = lambda func, *args, **kwargs: background_runner(background_tasks, func, *args, **kwargs)

    job = _service.submit_file(
        buffer,
        owner_id=current_user.id,
        filename=file_name,
        content_type=content_type,
        metadata={"content_type": content_type} if content_type else None,
        async_runner=async_runner,
    )
    payload = _service.serialize_job(job.job_id, owner_id=current_user.id, include_result=not async_mode)
    return _clean_payload(payload)


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, current_user=Depends(dependencies.get_current_user)):
    try:
        payload = _service.serialize_job(job_id, owner_id=current_user.id)
    except KeyError:
        raise HTTPException(status_code=404, detail="job 不存在")
    return _clean_payload(payload)


@router.get("/jobs")
async def list_jobs(current_user=Depends(dependencies.get_current_user)):
    payload = _service.list_jobs(owner_id=current_user.id)
    payload["jobs"] = [_clean_payload(job) for job in payload.get("jobs", [])]
    return payload


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, current_user=Depends(dependencies.get_current_user)):
    removed = _service.delete_job(job_id, owner_id=current_user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="job 不存在")
    return {"ok": True}


@router.get("/jobs/{job_id}/source")
async def get_job_source(
    job_id: str,
    start: int = Query(..., ge=0, description="原文字符起始位置"),
    end: Optional[int] = Query(None, description="原文字符结束位置（可选）"),
    window: int = Query(120, ge=0, le=2000, description="上下文窗口大小"),
    current_user=Depends(dependencies.get_current_user),
):
    try:
        payload = _service.get_source_snippet(
            job_id,
            owner_id=current_user.id,
            start=start,
            end=end,
            window=window,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="job 不存在或未保留原文")
    return payload
