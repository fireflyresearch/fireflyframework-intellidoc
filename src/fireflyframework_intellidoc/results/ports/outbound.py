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

"""Outbound ports for the results domain.

Abstracts persistence of processing jobs and document results
so the pipeline layer stays independent of the storage backend.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from fireflyframework_intellidoc.results.domain.processing_job import ProcessingJob
from fireflyframework_intellidoc.results.domain.processing_result import DocumentResult
from fireflyframework_intellidoc.types import JobStatus


@runtime_checkable
class ResultStoragePort(Protocol):
    """Port for persisting processing results."""

    # ── Jobs ──────────────────────────────────────────────────────────

    async def save_job(self, job: ProcessingJob) -> ProcessingJob: ...

    async def update_job(self, job: ProcessingJob) -> ProcessingJob: ...

    async def find_job_by_id(self, id: UUID) -> ProcessingJob | None: ...

    async def find_jobs(
        self,
        *,
        status: JobStatus | None = None,
        tenant_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[ProcessingJob], int]: ...

    async def delete_job(self, id: UUID) -> None: ...

    # ── Document Results ──────────────────────────────────────────────

    async def save_document_result(
        self, result: DocumentResult
    ) -> DocumentResult: ...

    async def find_document_results(
        self, job_id: UUID
    ) -> list[DocumentResult]: ...

    async def find_document_result(
        self, job_id: UUID, document_id: UUID
    ) -> DocumentResult | None: ...

    # ── Analytics ────────────────────────────────────────────────────

    async def count_jobs(
        self,
        *,
        status: JobStatus | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int: ...

    async def get_analytics_summary(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> dict[str, Any]: ...
