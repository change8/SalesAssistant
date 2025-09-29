from __future__ import annotations

from app.core.ai import AIRequirementAnalyzer
from app.models.api import ConstraintConfig
from app.models.domain import RequirementRecord


def test_ai_analyzer_falls_back_to_heuristic_when_no_llm():
    analyzer = AIRequirementAnalyzer(model="heuristic")
    requirement = RequirementRecord(
        identifier="1",
        project="航企应收系统",
        description="优化数据库接口性能，补充自动化测试",
        metadata={},
    )

    result = analyzer.analyze_requirement(requirement, config=ConstraintConfig(model="heuristic"))

    assert result.allocation["backend"] > 0
    assert result.allocation["test"] >= 0
    assert "启发式" in (result.analysis or "")
