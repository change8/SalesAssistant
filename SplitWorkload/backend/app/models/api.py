from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RoleAllocation(BaseModel):
    product: float = 0.0
    frontend: float = 0.0
    backend: float = 0.0
    test: float = 0.0
    ops: float = 0.0
    analysis: Optional[str] = Field(default=None, description="AI-provided reasoning for the allocation")


class RequirementResult(BaseModel):
    id: Optional[str] = Field(default=None, description="Identifier parsed from the spreadsheet, if available")
    project: Optional[str] = Field(default=None, description="Project or module name owning the requirement")
    requirement: str = Field(..., description="Demand description text")
    allocation: RoleAllocation


class SheetSummary(BaseModel):
    total_allocated: float = 0.0
    by_role: Dict[str, float] = Field(default_factory=dict)
    limit: Optional[float] = Field(default=None, description="Applied total workload limit")


class SheetResult(BaseModel):
    sheet_name: str
    total_months: Optional[float] = Field(default=None, description="Total workload constraint (person-months)")
    projects: List[RequirementResult]
    summary: SheetSummary


class AnalysisResponse(BaseModel):
    sheets: List[SheetResult]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConstraintConfig(BaseModel):
    strategy: str = Field(default="balanced", description="Allocation strategy label")
    total_limit: Optional[float] = Field(default=None, description="Override total workload limit")
    model: Optional[str] = Field(default="qwen3-coder", description="Preferred AI model identifier")
    roles: Optional[List[str]] = Field(default=None, description="Custom role definitions")


class AnalyzeRequest(BaseModel):
    config: ConstraintConfig = Field(default_factory=ConstraintConfig)
