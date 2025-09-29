from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from SplitWorkload.backend.app.models.api import ConstraintConfig
from SplitWorkload.backend.app.models.domain import RequirementAllocation, SheetAllocation, SheetPayload

_STANDARD_ROLES: Iterable[str] = ("product", "frontend", "backend", "test", "ops")


class AllocationOptimizer:
    """Apply workload constraints and compute sheet-level summaries."""

    def optimize(
        self,
        sheet: SheetPayload,
        allocations: List[RequirementAllocation],
        config: ConstraintConfig,
    ) -> SheetAllocation:
        limit = config.total_limit or sheet.total_constraint
        adjusted_allocations = allocations

        applied_limit = limit
        if limit is not None:
            adjusted_allocations = self._apply_limit(allocations, limit)
        else:
            applied_limit = self._allocation_total_sum(allocations)

        summary = self._build_summary(adjusted_allocations, applied_limit)

        return SheetAllocation(sheet=sheet, allocations=adjusted_allocations, summary=summary)

    def _apply_limit(
        self,
        allocations: List[RequirementAllocation],
        limit: float,
    ) -> List[RequirementAllocation]:
        total_requested = sum(self._allocation_total(item) for item in allocations)
        if total_requested <= 0 or total_requested <= limit:
            return allocations

        ratio = limit / total_requested
        adjusted: List[RequirementAllocation] = []

        for item in allocations:
            scaled_allocation = {
                role: round(value * ratio, 1)
                for role, value in item.allocation.items()
            }
            note = item.analysis or ""
            adjustment_note = f"总量约束：按{ratio:.2f}比例缩放分配"
            analysis = f"{note}；{adjustment_note}" if note else adjustment_note
            adjusted.append(
                RequirementAllocation(
                    requirement=item.requirement,
                    allocation=scaled_allocation,
                    analysis=analysis,
                )
            )

        return adjusted

    def _build_summary(
        self,
        allocations: List[RequirementAllocation],
        limit: Optional[float],
    ) -> Dict[str, object]:
        by_role: Dict[str, float] = {role: 0.0 for role in _STANDARD_ROLES}
        for item in allocations:
            for role, value in item.allocation.items():
                by_role[role] = round(by_role.get(role, 0.0) + float(value), 1)

        total = round(sum(by_role.values()), 1)
        payload: Dict[str, object] = {"total_allocated": total, "by_role": by_role}
        if limit is not None:
            payload["limit"] = float(limit)
        return payload

    def _allocation_total(self, allocation: RequirementAllocation) -> float:
        return float(sum(allocation.allocation.values()))

    def _allocation_total_sum(self, allocations: List[RequirementAllocation]) -> float:
        return sum(self._allocation_total(item) for item in allocations)
