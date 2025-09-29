from __future__ import annotations

from typing import List, Optional

from SplitWorkload.backend.app.core.ai import AIRequirementAnalyzer
from SplitWorkload.backend.app.core.allocation import AllocationOptimizer
from SplitWorkload.backend.app.core.excel import ExcelParser
from SplitWorkload.backend.app.core.exporter import ExcelExporter
from SplitWorkload.backend.app.models.api import (
    AnalysisResponse,
    ConstraintConfig,
    RequirementResult,
    RoleAllocation,
    SheetResult,
    SheetSummary,
)
from SplitWorkload.backend.app.models.domain import RequirementAllocation, SheetAllocation, SheetPayload


class WorkloadService:
    """Coordinates Excel parsing, AI requirement analysis, and workload allocation."""

    def __init__(
        self,
        excel_parser: Optional[ExcelParser] = None,
        ai_analyzer: Optional[AIRequirementAnalyzer] = None,
        optimizer: Optional[AllocationOptimizer] = None,
        exporter: Optional[ExcelExporter] = None,
    ) -> None:
        self._excel_parser = excel_parser or ExcelParser()
        self._ai_analyzer = ai_analyzer or AIRequirementAnalyzer()
        self._optimizer = optimizer or AllocationOptimizer()
        self._exporter = exporter or ExcelExporter()

    def process_workbook(
        self,
        file_bytes: bytes,
        filename: str,
        config: ConstraintConfig,
    ) -> AnalysisResponse:
        allocations = self._analyze_allocations(file_bytes=file_bytes, filename=filename, config=config)
        return self._build_response(filename=filename, config=config, allocations=allocations)

    def export_workbook(
        self,
        file_bytes: bytes,
        filename: str,
        config: ConstraintConfig,
    ) -> tuple[AnalysisResponse, bytes]:
        allocations = self._analyze_allocations(file_bytes=file_bytes, filename=filename, config=config)
        response = self._build_response(filename=filename, config=config, allocations=allocations)
        workbook_bytes = self._exporter.build_workbook(response)
        return response, workbook_bytes

    def _analyze_allocations(
        self,
        file_bytes: bytes,
        filename: str,
        config: ConstraintConfig,
    ) -> List[SheetAllocation]:
        sheets = self._excel_parser.parse_workbook(file_bytes=file_bytes, filename=filename)

        allocations: List[SheetAllocation] = []
        for sheet in sheets:
            sheet_allocations = self._run_sheet_allocation(sheet, config)
            allocations.append(sheet_allocations)
        return allocations

    def _build_response(
        self,
        filename: str,
        config: ConstraintConfig,
        allocations: List[SheetAllocation],
    ) -> AnalysisResponse:
        response_sheets = [self._sheet_to_response(sheet_alloc) for sheet_alloc in allocations]

        metadata = {"source_filename": filename}
        if config.model:
            metadata["model"] = config.model
        if config.strategy:
            metadata["strategy"] = config.strategy

        return AnalysisResponse(sheets=response_sheets, metadata=metadata)

    def _run_sheet_allocation(
        self,
        sheet: SheetPayload,
        config: ConstraintConfig,
    ) -> SheetAllocation:
        analyzed: List[RequirementAllocation] = [
            self._ai_analyzer.analyze_requirement(requirement, config=config)
            for requirement in sheet.requirements
        ]

        return self._optimizer.optimize(sheet=sheet, allocations=analyzed, config=config)

    def _sheet_to_response(self, allocation: SheetAllocation) -> SheetResult:
        projects = [self._requirement_to_response(item) for item in allocation.allocations]

        summary_payload = allocation.summary or {}
        total_allocated = float(summary_payload.get("total_allocated", 0.0))
        by_role = summary_payload.get("by_role", {})
        limit = summary_payload.get("limit", allocation.sheet.total_constraint)

        return SheetResult(
            sheet_name=allocation.sheet.name,
            total_months=limit,
            projects=projects,
            summary=SheetSummary(total_allocated=total_allocated, by_role=by_role, limit=limit),
        )

    def _requirement_to_response(self, allocation: RequirementAllocation) -> RequirementResult:
        role_allocation = self._build_role_allocation(allocation)
        requirement = allocation.requirement

        return RequirementResult(
            id=requirement.identifier,
            project=requirement.project,
            requirement=requirement.description,
            allocation=role_allocation,
        )

    def _build_role_allocation(self, allocation: RequirementAllocation) -> RoleAllocation:
        base_payload = allocation.allocation.copy()
        reason = allocation.analysis

        rounded_payload = {}
        for role in ("product", "frontend", "backend", "test", "ops"):
            value = float(base_payload.get(role, 0.0))
            rounded_payload[role] = round(value, 1)

        return RoleAllocation(**rounded_payload, analysis=reason)
