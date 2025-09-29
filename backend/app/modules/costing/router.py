"""API endpoints for cost estimation."""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.app.core import dependencies
from .schemas import CostEstimateResponse, CostingRequest
from .service import CostEstimator

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


@router.post("/analyze", response_model=CostEstimateResponse)
async def analyze_cost(
    current_user=Depends(dependencies.get_current_user),
    file: UploadFile = File(..., description="功能清单 Excel"),
    config: Optional[str] = Form(None, description="JSON 配置（费率/系数）"),
):
    request_model = _parse_config(config)
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="上传文件为空")

    return _service.estimate(
        file_bytes=file_bytes,
        filename=file.filename or "uploaded.xlsx",
        config=request_model.config,
    )
