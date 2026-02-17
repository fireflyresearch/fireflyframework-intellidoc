# Copyright 2026 Firefly Software Solutions Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Result application service.

Provides access to processing jobs and document results.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.exceptions import JobNotFoundException
from fireflyframework_intellidoc.results.domain.processing_job import ProcessingJob
from fireflyframework_intellidoc.results.domain.processing_result import (
    DocumentResult,
    ProcessingResult,
)
from fireflyframework_intellidoc.results.ports.outbound import ResultStoragePort
from fireflyframework_intellidoc.types import DocumentConfidence, JobStatus

logger = logging.getLogger(__name__)


@service
class ResultService:
    """Manages processing jobs and results."""

    def __init__(self, result_storage: ResultStoragePort) -> None:
        self._storage = result_storage

    # ── Jobs ──────────────────────────────────────────────────────────

    async def create_job(
        self,
        source_type: str,
        source_reference: str,
        filename: str,
        *,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> ProcessingJob:
        job = ProcessingJob(
            source_type=source_type,
            source_reference=source_reference,
            original_filename=filename,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            tags=tags or {},
        )
        return await self._storage.save_job(job)

    async def get_job(self, job_id: UUID) -> ProcessingJob:
        job = await self._storage.find_job_by_id(job_id)
        if job is None:
            raise JobNotFoundException(str(job_id))
        return job

    async def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        current_step: str = "",
        progress_percent: float | None = None,
        error_message: str | None = None,
    ) -> ProcessingJob:
        job = await self.get_job(job_id)
        job.status = status
        if current_step:
            job.current_step = current_step
        if progress_percent is not None:
            job.progress_percent = progress_percent
        if error_message is not None:
            job.error_message = error_message
        if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
            job.completed_at = datetime.now()
            if job.started_at:
                delta = job.completed_at - job.started_at
                job.processing_duration_ms = int(delta.total_seconds() * 1000)
        if status != JobStatus.PENDING and job.started_at is None:
            job.started_at = datetime.now()
        job.updated_at = datetime.now()
        return await self._storage.update_job(job)

    async def list_jobs(
        self,
        *,
        status: JobStatus | None = None,
        tenant_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[ProcessingJob], int]:
        return await self._storage.find_jobs(
            status=status,
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            size=size,
        )

    # ── Results ──────────────────────────────────────────────────────

    async def get_processing_result(self, job_id: UUID) -> ProcessingResult:
        job = await self.get_job(job_id)
        documents = await self._storage.find_document_results(job_id)

        total_fields = sum(len(d.extracted_fields) for d in documents)
        total_passed = sum(
            sum(1 for v in d.validation_results if v.passed)
            for d in documents
        )
        total_failed = sum(
            sum(1 for v in d.validation_results if not v.passed)
            for d in documents
        )

        scores = [
            d.overall_confidence.value for d in documents
        ]
        overall = DocumentConfidence.HIGH
        if scores:
            worst = min(scores)
            overall = DocumentConfidence(worst)

        return ProcessingResult(
            job=job,
            documents=documents,
            total_fields_extracted=total_fields,
            total_validations_passed=total_passed,
            total_validations_failed=total_failed,
            overall_confidence=overall,
        )

    async def get_document_result(
        self, job_id: UUID, document_id: UUID
    ) -> DocumentResult:
        result = await self._storage.find_document_result(job_id, document_id)
        if result is None:
            raise JobNotFoundException(f"{job_id}/{document_id}")
        return result

    # ── Analytics ─────────────────────────────────────────────────────

    async def get_analytics(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        return await self._storage.get_analytics_summary(from_date, to_date)
