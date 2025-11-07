"""Dispatch helpers for choosing the right extractor based on file type."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from zipfile import ZipFile

from .docx_extractor import extract_text_from_docx
from .ocr_extractor import ocr_image_or_pdf
from .pdf_extractor import extract_text_from_pdf
from .txt_extractor import extract_text_from_txt

logger = logging.getLogger(__name__)


def extract_text_from_file(path: str, filename: Optional[str] = None, content_type: Optional[str] = None) -> Tuple[str, Dict[str, str]]:
    """Return extracted text and metadata about the extraction."""

    detected = detect_file_type(path, filename, content_type)
    text = ""
    metadata: Dict[str, str] = {"detected_type": detected}
    try:
        metadata["byte_size"] = str(os.path.getsize(path))
    except Exception:
        metadata["byte_size"] = "unknown"

    logger.info(
        "extract_text_from_file start: detected=%s filename=%s content_type=%s size=%s path=%s",
        detected,
        filename or "",
        content_type or "",
        metadata.get("byte_size"),
        path,
    )

    if detected == "txt":
        text = extract_text_from_txt(path)
    elif detected == "docx":
        text = extract_text_from_docx(path)
    elif detected == "pdf":
        text = extract_text_from_pdf(path)
    else:
        # Fallback: best-effort text read
        text = extract_text_from_txt(path)
        metadata["fallback"] = "txt"

    stripped = text.strip()
    if not stripped:
        if detected == "pdf" or _looks_like_image(filename, path):
            ocr_text = ocr_image_or_pdf(path)
            if ocr_text.strip():
                text = ocr_text
                stripped = text.strip()
                metadata["ocr_used"] = "true"

    metadata["text_length"] = str(len(stripped))
    if not stripped:
        logger.warning(
            "extract_text_from_file empty: detected=%s filename=%s size=%s content_type=%s",
            detected,
            filename or "",
            metadata.get("byte_size"),
            content_type or "",
        )
    else:
        logger.info(
            "extract_text_from_file success: detected=%s filename=%s length=%s",
            detected,
            filename or "",
            metadata["text_length"],
        )

    return stripped, metadata


def detect_file_type(path: str, filename: Optional[str] = None, content_type: Optional[str] = None) -> str:
    ext = ""

    if filename:
        ext = Path(filename).suffix.lower()
    if not ext:
        ext = Path(path).suffix.lower()

    if content_type:
        if "pdf" in content_type:
            return "pdf"
        if "word" in content_type or "officedocument" in content_type:
            return "docx"
        if "text" in content_type or "plain" in content_type:
            return "txt"

    if ext in {".txt", ".md", ".text", ".json"}:
        return "txt"
    if ext in {".docx"}:
        return "docx"
    if ext in {".pdf"}:
        return "pdf"

    # Fallback: try signature-based detection when extension is missing
    signature = b""
    try:
        with open(path, "rb") as fh:
            signature = fh.read(8)
    except Exception:
        signature = b""

    if signature.startswith(b"%PDF"):
        return "pdf"

    if signature[:2] == b"PK":
        try:
            with ZipFile(path) as zf:
                # Heuristic: docx files must contain this entry
                if "word/document.xml" in zf.namelist():
                    return "docx"
        except Exception as exc:
            logger.debug("detect_file_type zip inspection failed: path=%s err=%s", path, exc)

    if signature:
        logger.debug("detect_file_type fallback signature=%s filename=%s content_type=%s", signature, filename, content_type)

    # Default to txt as a safe fallback
    return "txt"


def _looks_like_image(filename: Optional[str], path: str) -> bool:
    candidates = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    for target in (filename, path):
        if not target:
            continue
        if Path(str(target)).suffix.lower() in candidates:
            return True
    return False
