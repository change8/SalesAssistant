
import json
import logging
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional

import requests
from fastapi import UploadFile
from pdfminer.high_level import extract_text as extract_pdf_text
from docx import Document

from backend.app.core.config import settings
from backend.app.modules.bidding_v2.schemas import BiddingAnalysisResult, TimelineItem

logger = logging.getLogger(__name__)

CONTRACTS_DB_PATH = "data/contracts.db"

class BiddingService:
    def __init__(self):
        self.api_key = os.getenv("SA_DASHSCOPE_API_KEY")
        self.base_url = os.getenv("SA_DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = "qwen-plus" # Use a capable model

    async def analyze_document(self, file: UploadFile) -> BiddingAnalysisResult:
        # 1. Extract Text
        text = await self._extract_text(file)
        if not text:
            raise ValueError("无法提取文档内容")

        # 2. LLM Extraction
        extracted_data = self._call_llm_extraction(text[:50000])

        # 3. Match Requirements
        requirements = self._match_requirements(extracted_data.get("requirements", []))
        
        # 4. Calculate Score Estimate (if standard exists)
        total_score = sum(item.score_contribution for item in requirements)
        
        # 5. Assemble Result
        return BiddingAnalysisResult(
            requirements=requirements,
            has_scoring_standard=extracted_data.get("has_scoring_standard", False),
            total_score_estimate=total_score,
            disqualifiers=extracted_data.get("disqualifiers", []),
            timeline=[TimelineItem(**item) for item in extracted_data.get("timeline", [])],
            suggestions=extracted_data.get("suggestions", [])
        )

    async def _extract_text(self, file: UploadFile) -> str:
        content = await file.read()
        filename = file.filename.lower()
        
        if filename.endswith(".pdf"):
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as f:
                f.write(content)
            try:
                text = extract_pdf_text(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            return text
            
        elif filename.endswith(".docx"):
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as f:
                f.write(content)
            try:
                doc = Document(temp_path)
                text = "\n".join([p.text for p in doc.paragraphs])
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            return text
            
        elif filename.endswith(".txt"):
            return content.decode("utf-8", errors="ignore")
            
        return ""

    def _call_llm_extraction(self, text: str) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("No LLM API Key found. Returning mock data.")
            return self._get_mock_data()

        prompt = """
        你是一个专业的标书分析助手。请分析以下招标文件内容，提取关键要求和信息。
        
        请返回 JSON 对象，包含以下字段：
        1. requirements (list[dict]): 提取所有的硬性要求或评分项。
           每个条目包含：
           - category (str): "case" (业绩要求), "qualification" (企业资质/软著), "personnel" (人员要求)。
           - description (str): 要求描述（如“近三年类似业绩3个”、“拥有CMMI5证书”、“项目经理需PMP”）。
           - score_contribution (float): 如果有明确评分标准，该项对应的分值；否则为 0。
           - keywords (list[str]): 用于数据库匹配的关键词。
        2. has_scoring_standard (bool): 文档中是否明确包含了评分标准。
        3. disqualifiers (list[str]): 废标项或关键风险点。
        4. timeline (list[dict]): 包含 date (YYYY-MM-DD) 和 event (事件描述) 的时间轴。
        5. suggestions (list[str]): 其他重要建议。

        请只返回 JSON 对象。
        
        招标文件内容：
        """ + text[:10000]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是标书分析专家，请输出纯 JSON。"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            logger.error(f"LLM Call Failed: {e}")
            return self._get_mock_data()

    def _match_requirements(self, requirements: List[Dict[str, Any]]) -> List[Any]:
        """Match requirements against the database."""
        from backend.app.modules.bidding_v2.schemas import RequirementItem
        
        if not os.path.exists(CONTRACTS_DB_PATH):
            return []

        conn = sqlite3.connect(CONTRACTS_DB_PATH)
        cursor = conn.cursor()
        
        results = []
        for item in requirements:
            category = item.get("category", "case")
            keywords = item.get("keywords", [])
            score = item.get("score_contribution", 0)
            
            status = "unsatisfied"
            evidence = None
            
            if category == "personnel":
                status = "manual_check"
                evidence = "需人工核对人员简历"
            
            elif not keywords:
                status = "manual_check"
                evidence = "无法自动匹配"

            elif category == "case":
                # Match Contracts
                matched = []
                for kw in keywords:
                    if len(kw) < 2: continue
                    cursor.execute("SELECT title, contract_amount FROM contracts WHERE title LIKE ? LIMIT 3", (f"%{kw}%",))
                    rows = cursor.fetchall()
                    for row in rows:
                        matched.append(f"{row[0]} ({row[1]})")
                
                if matched:
                    status = "satisfied"
                    evidence = "匹配业绩：" + "; ".join(list(set(matched))[:3])
                
            elif category == "qualification":
                # Match Assets
                matched = []
                for kw in keywords:
                    cursor.execute("SELECT qualification_name FROM assets WHERE qualification_name LIKE ? LIMIT 1", (f"%{kw}%",))
                    row = cursor.fetchone()
                    if row:
                        matched.append(row[0])
                
                if matched:
                    status = "satisfied"
                    evidence = "拥有资质：" + "; ".join(list(set(matched)))

            results.append(RequirementItem(
                category=category,
                description=item["description"],
                status=status,
                evidence=evidence,
                score_contribution=score if status == "satisfied" else 0
            ))
            
        conn.close()
        return results

    def _get_mock_data(self):
        return {
            "has_scoring_standard": True,
            "requirements": [
                {"category": "case", "description": "近三年3个大数据项目", "score_contribution": 10, "keywords": ["大数据"]},
                {"category": "qualification", "description": "拥有CMMI5证书", "score_contribution": 5, "keywords": ["CMMI5"]},
                {"category": "personnel", "description": "项目经理PMP证书", "score_contribution": 2, "keywords": ["PMP"]}
            ],
            "disqualifiers": ["未提供近三年财务报表"],
            "timeline": [{"date": "2025-01-01", "event": "开标"}],
            "suggestions": ["注意付款周期"]
        }
