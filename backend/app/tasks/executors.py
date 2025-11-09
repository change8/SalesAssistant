"""Task executors for different job types."""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BiddingAnalysisExecutor:
    """Execute bidding analysis tasks."""

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bidding analysis.

        Args:
            payload: Task payload containing:
                - text: Optional text content to analyze
                - file_base64: Optional base64-encoded file
                - filename: Optional filename
                - content_type: Optional MIME type

        Returns:
            Analysis result dictionary

        Raises:
            ValueError: If payload is invalid
            RuntimeError: If analysis fails
        """
        from BiddingAssistant.backend.analyzer.tender_llm import TenderLLMAnalyzer
        from BiddingAssistant.backend.analyzer.llm_enhanced import EnhancedLLMClient
        from BiddingAssistant.backend.config import get_bidding_config
        from BiddingAssistant.backend.extractors.dispatcher import extract_text_from_file

        # Get configuration
        config = get_bidding_config()

        # Create enhanced LLM client
        llm_client = EnhancedLLMClient(
            provider=config.llm_provider,
            model=config.llm_model,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            timeout=config.llm_timeout,
            max_retries=3,
        )

        analyzer = TenderLLMAnalyzer(llm_client=llm_client)

        # Check if text or file provided
        text = payload.get("text")
        file_base64 = payload.get("file_base64")

        if text:
            # Direct text analysis
            logger.info("Analyzing direct text input")
            result = analyzer.analyze(text)

        elif file_base64:
            # File analysis
            filename = payload.get("filename", "document.pdf")
            content_type = payload.get("content_type")

            logger.info(f"Analyzing file: {filename}")

            # Decode base64 file
            file_bytes = base64.b64decode(file_base64)

            # Write to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                # Extract text from file
                extracted_text, meta = extract_text_from_file(
                    tmp_path,
                    filename=filename,
                    content_type=content_type,
                )

                if not extracted_text.strip():
                    raise RuntimeError("未能从文件中提取文本或文本为空")

                # Analyze extracted text
                result = analyzer.analyze(extracted_text)

                # Add metadata
                result["metadata"] = result.get("metadata", {})
                result["metadata"].update(meta or {})

            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        else:
            raise ValueError("Payload must contain either 'text' or 'file_base64'")

        logger.info("Bidding analysis completed successfully")
        return result


class WorkloadAnalysisExecutor:
    """Execute workload analysis tasks."""

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workload analysis.

        Args:
            payload: Task payload containing:
                - file_base64: Base64-encoded Excel file
                - filename: Excel filename
                - config: Optional analysis configuration

        Returns:
            Workload analysis result dictionary

        Raises:
            ValueError: If payload is invalid
            RuntimeError: If analysis fails
        """
        from SplitWorkload.backend.app.services.workload_service import WorkloadService
        from SplitWorkload.backend.app.models.api import ConstraintConfig

        file_base64 = payload.get("file_base64")
        if not file_base64:
            raise ValueError("Payload must contain 'file_base64'")

        filename = payload.get("filename", "workload.xlsx")
        config_dict = payload.get("config", {})

        logger.info(f"Analyzing workload file: {filename}")

        # Decode file
        file_bytes = base64.b64decode(file_base64)

        # Parse config
        config = ConstraintConfig(**config_dict)

        # Use enhanced LLM client in workload service
        service = WorkloadService()

        # Monkey-patch to use enhanced LLM client
        from SplitWorkload.backend.app.core.llm_client_enhanced import EnhancedQwenLLMClient
        from SplitWorkload.backend.app.core.ai_analyzer import AIRequirementAnalyzer

        # Replace LLM client in analyzer
        if hasattr(service, "_analyzer"):
            original_llm = service._analyzer._llm_client
            service._analyzer._llm_client = EnhancedQwenLLMClient(max_retries=3)

        result = service.process_workbook(
            file_bytes=file_bytes,
            filename=filename,
            config=config,
        )

        logger.info("Workload analysis completed successfully")
        return result.model_dump()


class CostEstimationExecutor:
    """Execute cost estimation tasks."""

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute cost estimation.

        Args:
            payload: Task payload containing:
                - file_base64: Base64-encoded Excel file
                - filename: Excel filename
                - config: Cost estimation configuration

        Returns:
            Cost estimation result dictionary

        Raises:
            ValueError: If payload is invalid
            RuntimeError: If estimation fails
        """
        from backend.app.modules.costing.service import CostEstimator
        from backend.app.modules.costing.schemas import CostingConfig

        file_base64 = payload.get("file_base64")
        if not file_base64:
            raise ValueError("Payload must contain 'file_base64'")

        filename = payload.get("filename", "cost_estimation.xlsx")
        config_dict = payload.get("config", {})

        logger.info(f"Estimating costs for file: {filename}")

        # Decode file
        file_bytes = base64.b64decode(file_base64)

        # Parse config
        config = CostingConfig(**config_dict)

        # Execute cost estimation
        estimator = CostEstimator()
        result = estimator.estimate(
            file_bytes=file_bytes,
            filename=filename,
            config=config,
        )

        logger.info("Cost estimation completed successfully")
        return result.model_dump()
