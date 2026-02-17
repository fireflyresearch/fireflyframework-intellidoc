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

"""In-memory implementation of the result storage port.

Used by the CLI to run the processing engine without a database.
Jobs and document results are held in memory for the duration of
the CLI invocation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fireflyframework_intellidoc.results.domain.processing_job import ProcessingJob
from fireflyframework_intellidoc.results.domain.processing_result import DocumentResult
from fireflyframework_intellidoc.types import JobStatus


class InMemoryResultStorage:
    """Dict-backed result storage for CLI use."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, ProcessingJob] = {}
        self._doc_results: dict[UUID, list[DocumentResult]] = {}

    # ── Jobs ──────────────────────────────────────────────────────────

    async def save_job(self, job: ProcessingJob) -> ProcessingJob:
        self._jobs[job.id] = job
        self._doc_results.setdefault(job.id, [])
        return job

    async def update_job(self, job: ProcessingJob) -> ProcessingJob:
        self._jobs[job.id] = job
        return job

    async def find_job_by_id(self, id: UUID) -> ProcessingJob | None:
        return self._jobs.get(id)

    async def find_jobs(
        self,
        *,
        status: JobStatus | None = None,
        tenant_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[ProcessingJob], int]:
        items = list(self._jobs.values())
        if status:
            items = [j for j in items if j.status == status]
        if tenant_id:
            items = [j for j in items if j.tenant_id == tenant_id]
        total = len(items)
        start = page * size
        return items[start : start + size], total

    async def delete_job(self, id: UUID) -> None:
        self._jobs.pop(id, None)
        self._doc_results.pop(id, None)

    # ── Document Results ──────────────────────────────────────────────

    async def save_document_result(self, result: DocumentResult) -> DocumentResult:
        self._doc_results.setdefault(result.job_id, []).append(result)
        return result

    async def find_document_results(self, job_id: UUID) -> list[DocumentResult]:
        return self._doc_results.get(job_id, [])

    async def find_document_result(
        self, job_id: UUID, document_id: UUID
    ) -> DocumentResult | None:
        for dr in self._doc_results.get(job_id, []):
            if dr.id == document_id:
                return dr
        return None

    # ── Analytics ────────────────────────────────────────────────────

    async def count_jobs(
        self,
        *,
        status: JobStatus | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        items = list(self._jobs.values())
        if status:
            items = [j for j in items if j.status == status]
        return len(items)

    async def get_analytics_summary(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]:
        return {
            "total_jobs": len(self._jobs),
            "total_documents": sum(len(v) for v in self._doc_results.values()),
        }
