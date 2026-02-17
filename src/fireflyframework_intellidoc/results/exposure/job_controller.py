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

"""REST controller for processing job tracking.

Provides endpoints for listing, viewing, and managing
processing jobs.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pyfly.container.stereotypes import rest_controller
from pyfly.web.mappings import (
    delete_mapping,
    get_mapping,
    request_mapping,
)
from pyfly.web.params import PathVar, QueryParam

from fireflyframework_intellidoc.catalog.exposure.schemas import PageResponse
from fireflyframework_intellidoc.results.exposure.schemas import (
    JobResponse,
    JobStatusResponse,
)
from fireflyframework_intellidoc.results.service import ResultService
from fireflyframework_intellidoc.types import JobStatus


@rest_controller
@request_mapping("/api/v1/intellidoc/jobs")
class JobController:
    """Track and manage processing jobs."""

    def __init__(self, result_service: ResultService) -> None:
        self._results = result_service

    @get_mapping("")
    async def list_jobs(
        self,
        status: QueryParam[JobStatus | None] = None,
        tenant_id: QueryParam[str | None] = None,
        from_date: QueryParam[datetime | None] = None,
        to_date: QueryParam[datetime | None] = None,
        page: QueryParam[int] = 0,
        size: QueryParam[int] = 20,
    ) -> PageResponse[JobResponse]:
        """List processing jobs with optional filters."""
        items, total = await self._results.list_jobs(
            status=status,
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
            page=page,
            size=size,
        )
        return PageResponse.of(
            [JobResponse.from_domain(j) for j in items],
            total,
            page,
            size,
        )

    @get_mapping("/{job_id}")
    async def get_job(self, job_id: PathVar[UUID]) -> JobResponse:
        """Get full details for a processing job."""
        job = await self._results.get_job(job_id)
        return JobResponse.from_domain(job)

    @get_mapping("/{job_id}/status")
    async def get_job_status(
        self, job_id: PathVar[UUID]
    ) -> JobStatusResponse:
        """Get lightweight status for polling.

        This endpoint returns minimal data optimized for
        frequent polling during async processing.
        """
        job = await self._results.get_job(job_id)
        return JobStatusResponse.from_domain(job)

    @delete_mapping("/{job_id}", status_code=204)
    async def cancel_job(self, job_id: PathVar[UUID]) -> None:
        """Cancel a pending or in-progress job.

        Only jobs that have not yet completed can be cancelled.
        """
        await self._results.update_job_status(
            job_id,
            JobStatus.CANCELLED,
            error_message="Cancelled by user",
        )
