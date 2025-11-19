
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
        extracted_data = self._call_llm_extraction(text[:50000]) # Limit context window

        # 3. DB Matching & Scoring
        business_score, business_details = self._calculate_business_score(extracted_data.get("project_keywords", []))
        tech_score, tech_details = self._calculate_tech_score(extracted_data.get("tech_requirements", []))
        
        total_score = business_score + tech_score
        
        # 4. Assemble Result
        return BiddingAnalysisResult(
            totalScore=total_score,
            businessScore=business_score,
            techScore=tech_score,
            disqualifiers=extracted_data.get("disqualifiers", []),
            timeline=[TimelineItem(**item) for item in extracted_data.get("timeline", [])],
            suggestions=extracted_data.get("suggestions", []),
            scoreDetails=f"商务得分详情：\n{business_details}\n\n技术得分详情：\n{tech_details}"
        )

    async def _extract_text(self, file: UploadFile) -> str:
        content = await file.read()
        filename = file.filename.lower()
        
        if filename.endswith(".pdf"):
            # Save to temp file for pdfminer
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
        你是一个专业的标书分析助手。请分析以下招标文件内容，提取关键信息并以 JSON 格式返回。
        
        需要提取的字段：
        1. project_keywords (list[str]): 项目的关键技术关键词（如：Java, 大数据, 智慧城市, 运维）。
        2. tech_requirements (list[str]): 具体的资质证书要求或软件著作权要求（如：CMMI5, ISO9001, 某某软件著作权）。
        3. disqualifiers (list[str]): 废标项或关键风险点（如：不满足等保三级，无近三年无违法记录声明）。
        4. timeline (list[dict]): 包含 date (YYYY-MM-DD) 和 event (事件描述) 的时间轴列表。
        5. suggestions (list[str]): 其他重要建议（如：运营期要求，驻场要求，付款方式风险）。

        请只返回 JSON 对象，不要包含 markdown 格式或其他废话。
        
        招标文件内容：
        """ + text[:10000] # Truncate to avoid token limit

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

    def _calculate_business_score(self, keywords: List[str]) -> tuple[int, str]:
        """Match keywords against contracts.db to find similar projects."""
        if not os.path.exists(CONTRACTS_DB_PATH):
            return 0, "数据库未连接"

        score = 0
        details = []
        
        conn = sqlite3.connect(CONTRACTS_DB_PATH)
        cursor = conn.cursor()
        
        # Simple keyword matching strategy
        matched_contracts = set()
        for kw in keywords:
            if len(kw) < 2: continue
            cursor.execute("SELECT title, contract_amount FROM contracts WHERE title LIKE ? LIMIT 3", (f"%{kw}%",))
            rows = cursor.fetchall()
            for row in rows:
                if row[0] not in matched_contracts:
                    matched_contracts.add(row[0])
                    score += 5 # 5 points per matched contract
                    details.append(f"匹配业绩：{row[0]} ({row[1]}) +5分")
        
        conn.close()
        
        final_score = min(40, score) # Cap at 40
        return final_score, "\n".join(details) if details else "无匹配业绩"

    def _calculate_tech_score(self, requirements: List[str]) -> tuple[int, str]:
        """Match requirements against assets in contracts.db."""
        if not os.path.exists(CONTRACTS_DB_PATH):
            return 0, "数据库未连接"

        score = 0
        details = []
        
        conn = sqlite3.connect(CONTRACTS_DB_PATH)
        cursor = conn.cursor()
        
        for req in requirements:
            # Fuzzy match for qualifications
            cursor.execute("SELECT qualification_name FROM assets WHERE qualification_name LIKE ? LIMIT 1", (f"%{req}%",))
            row = cursor.fetchone()
            if row:
                score += 5
                details.append(f"满足资质/软著：{row[0]} +5分")
            else:
                details.append(f"缺失资质/软著：{req} -0分")
        
        conn.close()
        
        final_score = min(50, score) # Cap at 50
        return final_score, "\n".join(details) if details else "无匹配资质要求"

    def _get_mock_data(self):
        return {
            "project_keywords": ["大数据", "运维"],
            "tech_requirements": ["CMMI5", "ISO9001"],
            "disqualifiers": ["未提供近三年财务报表"],
            "timeline": [{"date": "2025-01-01", "event": "开标"}],
            "suggestions": ["注意付款周期"]
        }
