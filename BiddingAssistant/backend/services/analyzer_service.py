"""High-level orchestration for running LLM-based tender analysis jobs."""

from __future__ import annotations

import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..analyzer.tender_llm import TenderLLMAnalyzer
from ..storage import AnalysisJobRecord, InMemoryJobStore
from ..extractors.dispatcher import extract_text_from_file


@dataclass
class JobPayload:
    """User-provided context for an analysis job."""

    text: Optional[str] = None
    filename: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalysisService:
    """Submit and execute analysis jobs with pluggable storage."""

    def __init__(self, analyzer: TenderLLMAnalyzer, store: Optional[InMemoryJobStore] = None) -> None:
        self.analyzer = analyzer
        self.store = store or InMemoryJobStore()

    # ------------------------------------------------------------------ API
    def create_job(
        self,
        source: str,
        *,
        owner_id: Optional[int] = None,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalysisJobRecord:
        job = AnalysisJobRecord(
            job_id=str(uuid.uuid4()),
            status="pending",
            source=source,
            owner_id=owner_id,
            filename=filename,
            metadata=metadata or {},
            created_at=time.time(),
        )
        return self.store.create(job)

    def process_text(
        self,
        job_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalysisJobRecord:
        job = self.store.get(job_id)
        if not job:
            raise KeyError(f"Job {job_id} not found")
        metadata = metadata or {}
        combined_metadata = dict(job.metadata)
        combined_metadata.update(metadata)
        combined_metadata.pop("preprocess", None)
        self.store.update(
            job_id,
            status="processing",
            started_at=time.time(),
            text_length=len(text),
            metadata=combined_metadata,
            source_text=text,
        )
        try:
            result = self.analyzer.analyze(text)
            combined_metadata.update(result.pop("metadata", {}))
            self.store.update(job_id, metadata=combined_metadata)
            self.store.update(job_id, status="completed", result=result, completed_at=time.time())
        except Exception as exc:  # pragma: no cover - defensive
            self.store.update(job_id, status="failed", error=str(exc), completed_at=time.time())
            raise
        finally:
            job = self.store.get(job_id)
        assert job is not None
        return job

    def process_file_upload(
        self,
        job_id: str,
        path: str,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> AnalysisJobRecord:
        text, meta = extract_text_from_file(path, filename=filename, content_type=content_type)
        if not text.strip():
            self.store.update(job_id, status="failed", error="未能从文件中提取文本或文本为空", completed_at=time.time())
            job = self.store.get(job_id)
            assert job is not None
            return job
        metadata = meta or {}
        if filename and "filename" not in metadata:
            metadata["filename"] = filename
        return self.process_text(job_id, text, metadata=metadata)

    # ---------------------------------------------------------------- Helpers
    def submit_text(
        self,
        *,
        owner_id: Optional[int] = None,
        text: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        async_runner: Optional[Any] = None,
    ) -> AnalysisJobRecord:
        job = self.create_job(source="text", owner_id=owner_id, filename=filename, metadata=metadata)
        if async_runner:
            async_runner(self.process_text, job.job_id, text, metadata)
            stored = self.store.get(job.job_id)
            assert stored is not None
            return stored
        return self.process_text(job.job_id, text, metadata)

    def submit_file(
        self,
        file_obj,
        *,
        owner_id: Optional[int] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        async_runner: Optional[Any] = None,
    ) -> AnalysisJobRecord:
        job = self.create_job(source="file", owner_id=owner_id, filename=filename, metadata=metadata)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_obj.read())
            tmp_path = tmp.name
        try:
            if async_runner:
                async_runner(self.process_file_upload, job.job_id, tmp_path, filename, content_type)
                stored = self.store.get(job.job_id)
                assert stored is not None
                return stored
            return self.process_file_upload(job.job_id, tmp_path, filename, content_type)
        finally:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

    # ---------------------------------------------------------------- Public read
    def serialize_job(self, job_id: str, *, owner_id: Optional[int] = None, include_result: bool = True) -> Dict[str, Any]:
        job = self.store.get(job_id)
        if not job or (owner_id is not None and job.owner_id != owner_id):
            raise KeyError(job_id)
        data = self._serialize_job_record(job, include_result=include_result)
        return data

    def list_jobs(self, *, owner_id: Optional[int] = None) -> Dict[str, Any]:
        if owner_id is not None:
            jobs_iterable = self.store.list_by_owner(owner_id)
        else:
            jobs_iterable = self.store.list()
        jobs = [
            self._serialize_job_record(j, include_result=False)
            for j in sorted(jobs_iterable, key=lambda x: x.created_at, reverse=True)
        ]
        return {"jobs": jobs}

    def delete_job(self, job_id: str, *, owner_id: Optional[int] = None) -> bool:
        job = self.store.get(job_id)
        if not job or (owner_id is not None and job.owner_id != owner_id):
            return False
        return self.store.delete(job_id)

    # ---------------------------------------------------------------- Internal
    @staticmethod
    def _serialize_job_record(job: AnalysisJobRecord, include_result: bool = True) -> Dict[str, Any]:
        payload = {
            "job_id": job.job_id,
            "status": job.status,
            "source": job.source,
            "filename": job.filename,
            "owner_id": job.owner_id,
            "text_length": job.text_length,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "metadata": job.metadata,
            "error": job.error,
            "has_source_text": bool(job.source_text),
        }
        if include_result and job.result is not None:
            payload["result"] = job.result
        return payload

    def get_source_snippet(
        self,
        job_id: str,
        *,
        owner_id: Optional[int] = None,
        start: int,
        end: Optional[int] = None,
        window: int = 120,
    ) -> Dict[str, Any]:
        job = self.store.get(job_id)
        if not job or job.source_text is None or (owner_id is not None and job.owner_id != owner_id):
            raise KeyError(job_id)
        text = job.source_text
        length = len(text)
        if length == 0:
            return {"job_id": job_id, "start": 0, "end": 0, "excerpt": "", "context": "", "length": 0}

        start = max(0, min(length, int(start)))
        if end is None:
            end = start + 1
        end = max(start, min(length, int(end)))
        window = max(0, int(window))
        excerpt = text[start:end]
        context_start = max(0, start - window)
        context_end = min(length, end + window)
        context = text[context_start:context_end]
        return {
            "job_id": job_id,
            "start": start,
            "end": end,
            "excerpt": excerpt,
            "context": context,
            "context_start": context_start,
            "context_end": context_end,
            "length": length,
        }


def background_runner(background_tasks, func, *args, **kwargs):
    """Helper that forwards execution to FastAPI BackgroundTasks if provided."""

    if background_tasks is None:
        raise RuntimeError("Background runner requires FastAPI BackgroundTasks instance")
    background_tasks.add_task(func, *args, **kwargs)
