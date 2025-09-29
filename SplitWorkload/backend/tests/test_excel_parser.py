from __future__ import annotations

import io

import pandas as pd

from app.core.excel import ExcelParser


def build_workbook_bytes() -> bytes:
    frame = pd.DataFrame(
        [
            {
                "序号": 1,
                "项目名称": "货运航企及物流应收管理选代开发项目",
                "业务需求说明": "优化现有资源使用率，推进微服务架构改造",
                "产品": "",
                "前端": "",
                "后端": "",
                "测试": "",
                "运维": "",
                "预估最低投入要求合计（单位：人月）": "",
            },
            {
                "序号": "合计",
                "项目名称": "",
                "业务需求说明": "",
                "产品": "",
                "前端": "",
                "后端": "",
                "测试": "",
                "运维": "",
                "预估最低投入要求合计（单位：人月）": 120,
            },
        ]
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="Sheet1")
    return buffer.getvalue()


def test_excel_parser_extracts_requirements_and_total():
    parser = ExcelParser()
    content = build_workbook_bytes()

    sheets = parser.parse_workbook(content, filename="sample.xlsx")

    assert len(sheets) == 1
    sheet = sheets[0]
    assert sheet.total_constraint == 120
    assert len(sheet.requirements) == 1

    requirement = sheet.requirements[0]
    assert requirement.project == "货运航企及物流应收管理选代开发项目"
    assert "row_total_constraint" in requirement.metadata
    assert requirement.metadata["row_total_constraint"] is None
