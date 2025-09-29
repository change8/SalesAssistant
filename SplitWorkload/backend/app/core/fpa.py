from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from app.models.domain import RequirementRecord

_TRANSACTION_KEYWORDS = {
    "ei": {"录入", "输入", "新增", "提交", "导入", "采集"},
    "eo": {"输出", "报表", "导出", "通知", "推送"},
    "eq": {"查询", "检索", "搜索", "统计", "分析"},
}

_DATA_FUNCTION_KEYWORDS = {
    "ilf": {"主数据", "数据库", "表", "档案", "配置", "存储"},
    "eif": {"外部", "第三方", "共享", "对接", "同步"},
}

_ROLE_COMPLEXITY_HINTS = {
    "product": {"规划", "需求", "流程", "原型", "评审"},
    "frontend": {"页面", "ui", "可视化", "交互", "前端", "响应式"},
    "backend": {"接口", "api", "服务", "数据", "计算", "任务", "队列", "微服务"},
    "test": {"测试", "用例", "验证", "质量", "回归", "覆盖"},
    "ops": {"部署", "运维", "监控", "日志", "告警", "ci/cd", "发布"},
}

_COMPLEXITY_LEVELS = [
    ("低", 0, 60),
    ("中", 60, 180),
    ("高", 180, 1000),
]


@dataclass(slots=True)
class FPAInsight:
    function_type: str
    data_complexity: str
    transaction_complexity: str
    estimated_function_points: float
    role_weight_hint: Dict[str, float]

    def to_prompt_fragment(self) -> str:
        weights = ", ".join(f"{role}: {weight:.2f}" for role, weight in self.role_weight_hint.items())
        return (
            f"功能类型: {self.function_type}；数据复杂度: {self.data_complexity}；"
            f"交易复杂度: {self.transaction_complexity}；功能点估算: {self.estimated_function_points:.1f}。"
            f"角色权重提示: {weights}。"
        )


def analyze_with_nesma_framework(requirement: RequirementRecord) -> FPAInsight:
    description = (requirement.description or "").lower()

    function_type = _guess_function_type(description)
    data_complexity = _guess_data_complexity(description)
    transaction_complexity = _guess_transaction_complexity(description)

    base_points = {
        "低": 3.0,
        "中": 7.0,
        "高": 10.0,
    }
    estimated_fp = (base_points.get(data_complexity, 5.0) + base_points.get(transaction_complexity, 5.0)) / 2.0

    role_weights = _estimate_role_weights(description, function_type, transaction_complexity)

    return FPAInsight(
        function_type=function_type,
        data_complexity=data_complexity,
        transaction_complexity=transaction_complexity,
        estimated_function_points=estimated_fp,
        role_weight_hint=role_weights,
    )


def _guess_function_type(text: str) -> str:
    for type_code, keywords in _DATA_FUNCTION_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            return type_code.upper()
    for type_code, keywords in _TRANSACTION_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            return type_code.upper()
    return "MIXED"


def _guess_data_complexity(text: str) -> str:
    length = len(text)
    for label, lower, upper in _COMPLEXITY_LEVELS:
        if lower <= length < upper:
            return label
    return "高"


def _guess_transaction_complexity(text: str) -> str:
    score = 0
    for keywords in _TRANSACTION_KEYWORDS.values():
        for keyword in keywords:
            if keyword.lower() in text:
                score += 1
    if score <= 1:
        return "低"
    if score == 2:
        return "中"
    return "高"


def _estimate_role_weights(text: str, function_type: str, complexity: str) -> Dict[str, float]:
    weights: Dict[str, float] = {role: 0.0 for role in _ROLE_COMPLEXITY_HINTS}
    for role, keywords in _ROLE_COMPLEXITY_HINTS.items():
        count = sum(text.count(keyword.lower()) for keyword in keywords)
        if count:
            weights[role] = float(count)

    # ensure backend/front weights based on function type heuristics
    if function_type in {"ILF", "EIF"}:
        weights["backend"] += 2.0
    if function_type in {"EO", "EQ"}:
        weights["frontend"] += 1.5
        weights["backend"] += 1.0
    if function_type == "EI":
        weights["product"] += 1.0
        weights["test"] += 0.5

    complexity_boost = {"低": 0.5, "中": 1.0, "高": 1.5}.get(complexity, 1.0)
    weights["backend"] += complexity_boost
    weights["test"] += complexity_boost / 2

    total = sum(weights.values())
    if total == 0:
        return {role: 1.0 if role == "backend" else 0.2 for role in weights}

    return {role: round(value / total, 2) for role, value in weights.items()}
