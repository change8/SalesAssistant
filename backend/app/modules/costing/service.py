"""Cost estimation service built on top of SplitWorkload analysis."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Tuple

from SplitWorkload.backend.app.models.api import AnalysisResponse, ConstraintConfig
from SplitWorkload.backend.app.services.workload_service import WorkloadService

from .schemas import CostEstimateResponse, CostingConfig, RequirementCost, SheetCostResult, SheetCostSummary

DEFAULT_RATES: Dict[str, float] = {
    "architect": 18000.0,
    "project_manager": 16000.0,
    "product_design": 12000.0,
    "backend_dev": 15000.0,
    "frontend_dev": 14000.0,
    "qa": 11000.0,
    "implementation": 10000.0,
}

ROLE_KEYS = {
    "product": "product_design",
    "backend": "backend_dev",
    "frontend": "frontend_dev",
    "test": "qa",
    "ops": "implementation",
}


class CostEstimator:
    """Derive role-based workload and cost estimations from workload analysis."""

    def __init__(self, workload_service: WorkloadService | None = None) -> None:
        self._workload_service = workload_service or WorkloadService()

    def estimate(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        config: CostingConfig,
    ) -> CostEstimateResponse:
        constraint = self._sanitize_constraint(config.constraint)
        workload = self._workload_service.process_workbook(
            file_bytes=file_bytes,
            filename=filename,
            config=constraint,
        )
        rates = self._merge_rates(config.rates)
        return self._build_response(workload, rates, config)

    # ------------------------------------------------------------------ helpers
    def _sanitize_constraint(self, constraint: ConstraintConfig) -> ConstraintConfig:
        # ensure strategy/model fallbacks from workload defaults
        payload = constraint.model_dump()
        if not payload.get("model"):
            payload["model"] = "qwen3-max"
        return ConstraintConfig(**payload)

    def _merge_rates(self, custom_rates: Dict[str, float] | None) -> Dict[str, float]:
        rates = DEFAULT_RATES.copy()
        if custom_rates:
            for key, value in custom_rates.items():
                try:
                    rates[key] = float(value)
                except (TypeError, ValueError):
                    continue
        return rates

    def _expand_allocations(
        self,
        raw: Dict[str, float],
        *,
        architect_ratio: float,
        project_manager_ratio: float,
    ) -> Dict[str, float]:
        expanded: Dict[str, float] = {role: 0.0 for role in DEFAULT_RATES.keys()}
        for source_key, target_key in ROLE_KEYS.items():
            expanded[target_key] = round(float(raw.get(source_key, 0.0)), 3)

        tech_total = expanded["backend_dev"] + expanded["frontend_dev"] + expanded["implementation"]
        base_total = tech_total + expanded["product_design"] + expanded["qa"]
        expanded["architect"] = round(tech_total * architect_ratio, 3)
        expanded["project_manager"] = round(base_total * project_manager_ratio, 3)
        return expanded

    def _cost_from_allocations(self, allocations: Dict[str, float], rates: Dict[str, float]) -> Tuple[Dict[str, float], float]:
        costs: Dict[str, float] = {}
        total_cost = 0.0
        for role, months in allocations.items():
            rate = rates.get(role, DEFAULT_RATES.get(role, 0.0))
            cost = round(months * rate, 2)
            costs[role] = cost
            total_cost += cost
        return costs, round(total_cost, 2)

    def _build_response(
        self,
        workload: AnalysisResponse,
        rates: Dict[str, float],
        config: CostingConfig,
    ) -> CostEstimateResponse:
        sheets: list[SheetCostResult] = []
        global_months = defaultdict(float)
        global_costs = defaultdict(float)

        for sheet in workload.sheets:
            projects: list[RequirementCost] = []
            sheet_months = defaultdict(float)
            sheet_costs = defaultdict(float)

            for requirement in sheet.projects:
                allocation_dict = requirement.allocation.model_dump()  # includes analysis
                analysis = allocation_dict.pop("analysis", None)
                expanded = self._expand_allocations(
                    allocation_dict,
                    architect_ratio=config.architect_ratio,
                    project_manager_ratio=config.project_manager_ratio,
                )
                costs, total_cost = self._cost_from_allocations(expanded, rates)
                total_person_months = round(sum(expanded.values()), 3)

                for role, value in expanded.items():
                    sheet_months[role] += value
                    global_months[role] += value
                for role, value in costs.items():
                    sheet_costs[role] += value
                    global_costs[role] += value

                projects.append(
                    RequirementCost(
                        id=requirement.id,
                        project=requirement.project,
                        requirement=requirement.requirement,
                        allocations={k: round(v, 3) for k, v in expanded.items()},
                        cost_breakdown=costs,
                        total_person_months=round(total_person_months, 3),
                        total_cost=total_cost,
                        analysis=analysis,
                    )
                )

            sheet_summary = SheetCostSummary(
                total_person_months=round(sum(sheet_months.values()), 3),
                total_cost=round(sum(sheet_costs.values()), 2),
                by_role_months={k: round(v, 3) for k, v in sheet_months.items()},
                by_role_cost={k: round(v, 2) for k, v in sheet_costs.items()},
            )

            sheets.append(
                SheetCostResult(
                    sheet_name=sheet.sheet_name,
                    projects=projects,
                    summary=sheet_summary,
                )
            )

        metadata = workload.metadata.copy()
        metadata.setdefault("source", "SplitWorkload")

        assumptions = {
            "architect_ratio": config.architect_ratio,
            "project_manager_ratio": config.project_manager_ratio,
            "notes": "架构师按技术人月比例推导，项目经理按总人月比例推导",
        }

        return CostEstimateResponse(
            sheets=sheets,
            metadata=metadata,
            rates=rates,
            assumptions=assumptions,
        )
