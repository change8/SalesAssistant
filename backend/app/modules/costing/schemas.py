"""Pydantic schemas for cost estimation responses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from SplitWorkload.backend.app.models.api import ConstraintConfig

DEFAULT_ROLE_ORDER = [
    "architect",
    "project_manager",
    "product_design",
    "backend_dev",
    "frontend_dev",
    "qa",
    "implementation",
]


class CostingConfig(BaseModel):
    constraint: ConstraintConfig = Field(default_factory=ConstraintConfig)
    rates: Dict[str, float] = Field(default_factory=dict)
    architect_ratio: float = 0.12
    project_manager_ratio: float = 0.15


class CostingRequest(BaseModel):
    config: CostingConfig = Field(default_factory=CostingConfig)


class RequirementCost(BaseModel):
    id: Optional[str] = None
    project: Optional[str] = None
    requirement: str
    allocations: Dict[str, float]
    cost_breakdown: Dict[str, float]
    total_person_months: float
    total_cost: float
    analysis: Optional[str] = None


class SheetCostSummary(BaseModel):
    total_person_months: float
    total_cost: float
    by_role_months: Dict[str, float]
    by_role_cost: Dict[str, float]


class SheetCostResult(BaseModel):
    sheet_name: str
    projects: List[RequirementCost]
    summary: SheetCostSummary


class CostEstimateResponse(BaseModel):
    sheets: List[SheetCostResult]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    rates: Dict[str, float] = Field(default_factory=dict)
    assumptions: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            float: lambda v: round(v, 4),
        }
