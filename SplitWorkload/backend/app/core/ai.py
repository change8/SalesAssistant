from __future__ import annotations

from typing import Dict, Iterable, Optional

from app.core.fpa import analyze_with_nesma_framework
from app.core.llm_client import LLMNotConfiguredError, LLMResponseFormatError, LLMResult, QwenLLMClient
from app.models.api import ConstraintConfig
from app.models.domain import RequirementAllocation, RequirementRecord

_ROLE_KEYWORDS: Dict[str, Iterable[str]] = {
    "backend": ["api", "接口", "数据库", "service", "数据", "算法", "后端"],
    "frontend": ["页面", "ui", "交互", "前端", "界面", "体验", "可视化"],
    "product": ["需求", "原型", "流程", "用户故事", "竞品", "产品"],
    "test": ["测试", "用例", "自动化", "性能", "安全"],
    "ops": ["部署", "监控", "运维", "ci", "cd", "docker", "k8s"],
}

_DEFAULT_EFFORT = 1.0  # person-months per requirement baseline placeholder


class AIRequirementAnalyzer:
    """Combine Qwen3-Max 大模型与 NESMA 功能点分析框架，计算需求工作量。"""

    def __init__(
        self,
        model: str | None = None,
        *,
        llm_client: Optional[QwenLLMClient] = None,
    ) -> None:
        self._model = (model or "qwen3-max").lower()
        self._llm_client = llm_client or QwenLLMClient()

    def analyze_requirement(
        self,
        requirement: RequirementRecord,
        config: ConstraintConfig,
    ) -> RequirementAllocation:
        fpa_insight = analyze_with_nesma_framework(requirement)
        prompt = self._build_prompt(requirement, config, fpa_insight.to_prompt_fragment())

        llm_result: Optional[LLMResult] = None
        llm_error: Optional[str] = None
        preferred_model = (config.model or self._model).lower()
        if preferred_model != "heuristic":
            try:
                llm_result = self._llm_client.analyze(prompt=prompt)
            except (LLMNotConfiguredError, LLMResponseFormatError, Exception) as exc:
                llm_error = str(exc)
                llm_result = None

        if llm_result:
            allocation = self._ensure_roles(llm_result.allocations)
            analysis = llm_result.analysis or "来自 Qwen3-Max 的分析"
            enriched_analysis = f"{analysis}；NESMA提示：{fpa_insight.to_prompt_fragment()}"
            return RequirementAllocation(
                requirement=requirement,
                allocation=allocation,
                analysis=enriched_analysis,
            )

        fallback_allocation = self._fallback_allocation(requirement, fpa_insight)
        analysis = self._build_reason(fallback_allocation)
        if llm_error:
            analysis = f"{analysis}（LLM 调用失败，已降级：{llm_error[:80]}）"
        analysis = f"启发式估算：{analysis}；NESMA提示：{fpa_insight.to_prompt_fragment()}"

        return RequirementAllocation(
            requirement=requirement,
            allocation=fallback_allocation,
            analysis=analysis,
        )

    def _build_prompt(self, requirement: RequirementRecord, config: ConstraintConfig, fpa_fragment: str) -> str:
        project_name = requirement.project or requirement.metadata.get("项目名称") or ""
        description = requirement.description
        strategy = config.strategy or "balanced"
        return (
            "目标：基于 NESMA 功能点分析与软件造价理论，对需求进行角色人月拆分。\n"
            "步骤：\n"
            "1. 结合给定的 NESMA/FPA 提示和需求文本，说明关键功能点及复杂度。\n"
            "2. 输出 JSON，字段包括 product、frontend、backend、test、ops、analysis。\n"
            "3. analysis 字段请总结拆分理由及复杂度判断。\n"
            "4. 所有数值单位为人月，允许保留一位小数。若某个角色不涉及请返回 0。\n"
            "5. 拆分策略可理解为 {strategy}。\n"
            "NESMA/FPA 提示：" + fpa_fragment + "\n"
            "需求所属项目：" + project_name + "\n"
            "需求描述：" + description + "\n"
            "请严格返回 JSON。"
        )

    def _fallback_allocation(self, requirement: RequirementRecord, fpa_insight) -> Dict[str, float]:
        keyword_scores = self._score_roles(requirement.description)
        keyword_weights = self._normalize_scores(keyword_scores, base_effort=1.0)

        combined_weights: Dict[str, float] = {}
        for role in _ROLE_KEYWORDS.keys():
            combined_weights[role] = round(
                0.6 * keyword_weights.get(role, 0.0) + 0.4 * fpa_insight.role_weight_hint.get(role, 0.0),
                3,
            )

        total = sum(combined_weights.values())
        if total == 0.0:
            combined_weights["backend"] = 1.0
            total = 1.0

        scale = max(fpa_insight.estimated_function_points / 5.0, 1.0)
        allocation = {
            role: round(_DEFAULT_EFFORT * scale * (weight / total), 1)
            for role, weight in combined_weights.items()
        }
        return self._ensure_roles(allocation)

    def _score_roles(self, text: str | None) -> Dict[str, float]:
        scores: Dict[str, float] = {role: 0.0 for role in _ROLE_KEYWORDS}
        if not text:
            return scores
        lowered = text.lower()
        for role, keywords in _ROLE_KEYWORDS.items():
            count = sum(lowered.count(keyword.lower()) for keyword in keywords)
            if count:
                scores[role] = float(count)
        return scores

    def _normalize_scores(self, scores: Dict[str, float], base_effort: float) -> Dict[str, float]:
        total = sum(scores.values())
        if total == 0.0:
            return {role: 0.0 for role in scores}
        normalized: Dict[str, float] = {}
        for role, score in scores.items():
            normalized[role] = round(base_effort * (score / total), 3)
        return normalized

    def _build_reason(self, scores: Dict[str, float]) -> str:
        ranked = [role for role, value in sorted(scores.items(), key=lambda item: item[1], reverse=True) if value > 0]
        if not ranked:
            return "未检测到明确关键词，使用默认分配。"
        role_descriptions = {
            "backend": "涉及接口、数据或核心逻辑",
            "frontend": "包含界面或交互调整",
            "product": "需要产品规划或需求澄清",
            "test": "需要测试覆盖或质量保障",
            "ops": "涉及部署、监控或CI/CD",
        }
        fragments = [role_descriptions.get(role, role) for role in ranked]
        return "；".join(fragments)

    def _ensure_roles(self, scores: Dict[str, float]) -> Dict[str, float]:
        payload = {role: round(float(scores.get(role, 0.0)), 1) for role in _ROLE_KEYWORDS}
        return payload
