from __future__ import annotations

import io
import re
from typing import Dict, List, Optional

import pandas as pd

from app.models.domain import RequirementRecord, SheetPayload

_PROJECT_KEYWORDS = {"project", "项目", "模块", "所属"}
_REQUIREMENT_KEYWORDS = {
    "requirement",
    "需求",
    "描述",
    "说明",
    "功能",
    "feature",
    "story",
}
_IDENTIFIER_KEYWORDS = {"id", "编号", "序号"}
_TOTAL_KEYWORDS = {"合计", "总计", "total", "限制", "限额"}
_TOTAL_AMOUNT_HEADERS = {
    "预估最低投入要求合计",
    "合计（单位：人月）",
    "合计(单位：人月)",
    "合计",
}

_ROLE_HEADERS = {
    "产品": "product",
    "前端": "frontend",
    "后端": "backend",
    "测试": "test",
    "运维": "ops",
}


class ExcelParser:
    """Parse uploaded Excel workbooks into normalized sheet payloads."""

    def parse_workbook(self, file_bytes: bytes, filename: str) -> List[SheetPayload]:
        """Return parsed sheets with lightweight heuristics.

        The current implementation is intentionally conservative: it attempts to detect
        common column patterns, but falls back to generic columns when faced with an
        unfamiliar layout. This keeps the pipeline usable while leaving room for the
        smarter structure detection described in the specification.
        """

        buffer = io.BytesIO(file_bytes)

        try:
            sheets = pd.read_excel(buffer, sheet_name=None, dtype=str)
        except Exception as exc:  # pragma: no cover - pass parsing issues upstream
            raise ValueError(f"Failed to read Excel file '{filename}': {exc}") from exc

        payloads: List[SheetPayload] = []
        for sheet_name, frame in sheets.items():
            cleaned = frame.dropna(how="all")
            requirements = self._extract_requirements(cleaned)
            constraint = self._extract_total_constraint(cleaned)
            metadata = {
                "column_headers": [str(col) for col in cleaned.columns],
                "row_count": len(cleaned.index),
            }
            payloads.append(
                SheetPayload(
                    name=str(sheet_name),
                    requirements=requirements,
                    total_constraint=constraint,
                    metadata=metadata,
                )
            )

        return payloads

    def _extract_requirements(self, frame: pd.DataFrame) -> List[RequirementRecord]:
        if frame.empty:
            return []

        identifier_col = self._find_column(frame, _IDENTIFIER_KEYWORDS)
        project_col = self._find_column(frame, _PROJECT_KEYWORDS)
        description_col = self._find_column(frame, _REQUIREMENT_KEYWORDS) or project_col or frame.columns[0]
        total_column = self._find_column(frame, _TOTAL_AMOUNT_HEADERS)

        role_columns: Dict[str, str] = {}
        for header, role in _ROLE_HEADERS.items():
            column = self._find_exact_column(frame, header)
            if column:
                role_columns[role] = column

        requirements: List[RequirementRecord] = []
        for _, row in frame.iterrows():
            description = self._cell_to_text(row.get(description_col))
            if not description:
                continue

            if self._is_total_row(row):
                continue

            identifier = self._cell_to_text(row.get(identifier_col)) if identifier_col else None
            project = self._cell_to_text(row.get(project_col)) if project_col else None

            metadata = {str(col): self._cell_to_text(row.get(col)) for col in frame.columns}
            if total_column:
                metadata["row_total_constraint"] = self._cell_to_float(row.get(total_column))
            for role, column in role_columns.items():
                metadata[f"role_{role}"] = self._cell_to_float(row.get(column))

            requirements.append(
                RequirementRecord(
                    identifier=identifier,
                    project=project,
                    description=description,
                    metadata=metadata,
                )
            )

        return requirements

    def _extract_total_constraint(self, frame: pd.DataFrame) -> Optional[float]:
        total_column = self._find_column(frame, _TOTAL_AMOUNT_HEADERS)
        if total_column:
            for _, row in frame.iterrows():
                if self._is_total_row(row):
                    return self._cell_to_float(row.get(total_column))

        for _, row in frame.iterrows():
            for value in row:
                workload = self._parse_workload_value(value)
                if workload is not None:
                    return workload
        return None

    def _parse_workload_value(self, value: object) -> Optional[float]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = self._cell_to_text(value)
        if not text:
            return None

        if not any(keyword in text.lower() for keyword in (kw.lower() for kw in _TOTAL_KEYWORDS)):
            return None

        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if not match:
            return None

        amount = float(match.group(1))
        lowered = text.lower()
        if "人天" in lowered:
            return amount / 20.0
        if "人时" in lowered or "人小时" in lowered:
            return amount / 160.0
        return amount

    def _find_column(self, frame: pd.DataFrame, keywords: set[str]) -> Optional[str]:
        lowered = {str(col).strip().lower(): col for col in frame.columns}
        for keyword in keywords:
            for normalized, original in lowered.items():
                if keyword.lower() in normalized:
                    return original
        return None

    def _find_exact_column(self, frame: pd.DataFrame, header: str) -> Optional[str]:
        for col in frame.columns:
            if str(col).strip() == header:
                return col
        return None

    def _is_total_row(self, row: pd.Series) -> bool:
        return any("合计" in self._cell_to_text(value) or "总计" in self._cell_to_text(value) for value in row)

    def _cell_to_text(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and pd.isna(value):
            return ""
        return str(value).strip()

    def _cell_to_float(self, value: object) -> Optional[float]:
        text = self._cell_to_text(value)
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            parsed = self._parse_workload_value(text)
            return parsed
