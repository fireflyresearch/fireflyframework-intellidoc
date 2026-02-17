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

"""REST controller for document processing submission.

Provides endpoints to submit documents for IDP processing — either
synchronously (waiting for results) or asynchronously (returning a
job ID for later polling).
"""

from __future__ import annotations

import logging

from pydantic import BaseModel
from pyfly.container.stereotypes import rest_controller
from pyfly.web.mappings import get_mapping, post_mapping, request_mapping
from pyfly.web.params import Body, Valid

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.pipeline.orchestrator import ProcessingOrchestrator
from fireflyframework_intellidoc.results.exposure.schemas import (
    BatchProcessRequest,
    BatchProcessResponse,
    FailedSubmission,
    ProcessingResultResponse,
    ProcessRequest,
    ProcessResponse,
)

logger = logging.getLogger(__name__)


class SourceInfo(BaseModel):
    """Information about a supported ingestion source."""

    source_type: str
    description: str
    example: str


@rest_controller
@request_mapping("/api/v1/intellidoc/process")
class ProcessingController:
    """Submit documents for IDP processing."""

    def __init__(
        self,
        config: IntelliDocConfig,
        orchestrator: ProcessingOrchestrator,
    ) -> None:
        self._config = config
        self._orchestrator = orchestrator

    @post_mapping("", status_code=202)
    async def process_document(
        self, dto: Valid[Body[ProcessRequest]]
    ) -> ProcessResponse:
        """Submit a single document for processing.

        In synchronous mode (``async_mode=false``), blocks until
        processing completes and returns the full result.
        In asynchronous mode, returns immediately with a job ID.
        """
        if dto.async_mode:
            job_id = await self._orchestrator.submit(
                source_type=dto.source_type,
                source_reference=dto.source_reference,
                filename=dto.filename,
                expected_type=dto.expected_type,
                expected_nature=dto.expected_nature,
                splitting_strategy=dto.splitting_strategy,
                target_schema=dto.target_schema,
                document_types=dto.document_types or None,
                tenant_id=dto.tenant_id,
                correlation_id=dto.correlation_id,
                tags=dto.tags,
            )
            return ProcessResponse.accepted(job_id=job_id)

        result = await self._orchestrator.process(
            source_type=dto.source_type,
            source_reference=dto.source_reference,
            filename=dto.filename,
            expected_type=dto.expected_type,
            expected_nature=dto.expected_nature,
            splitting_strategy=dto.splitting_strategy,
            target_schema=dto.target_schema,
            document_types=dto.document_types or None,
            tenant_id=dto.tenant_id,
            correlation_id=dto.correlation_id,
            tags=dto.tags,
        )
        return ProcessResponse.completed(
            job_id=result.job.id,
            result=ProcessingResultResponse.from_domain(result),
        )

    @post_mapping("/batch", status_code=202)
    async def process_batch(
        self, dto: Valid[Body[BatchProcessRequest]]
    ) -> BatchProcessResponse:
        """Submit multiple documents for asynchronous processing."""
        jobs: list[ProcessResponse] = []
        failures: list[FailedSubmission] = []

        for i, item in enumerate(dto.items):
            try:
                job_id = await self._orchestrator.submit(
                    source_type=item.source_type,
                    source_reference=item.source_reference,
                    filename=item.filename,
                    expected_type=item.expected_type,
                    expected_nature=item.expected_nature,
                    splitting_strategy=item.splitting_strategy,
                    target_schema=item.target_schema,
                    document_types=item.document_types or None,
                    tenant_id=item.tenant_id,
                    correlation_id=item.correlation_id,
                    tags=item.tags,
                )
                jobs.append(ProcessResponse.accepted(job_id=job_id))
            except Exception as exc:
                logger.error(
                    "Failed to submit batch item %d (%s): %s",
                    i, item.filename, exc,
                )
                failures.append(
                    FailedSubmission(
                        index=i,
                        filename=item.filename,
                        error_code=getattr(exc, "code", "SUBMISSION_ERROR"),
                        error_message=str(exc),
                    )
                )
                if dto.stop_on_failure:
                    break

        return BatchProcessResponse(
            total_submitted=len(jobs),
            jobs=jobs,
            failed_submissions=failures,
        )

    @get_mapping("/supported-sources")
    async def list_supported_sources(self) -> list[SourceInfo]:
        """Return the list of enabled ingestion source types."""
        sources = []
        if self._config.ingestion_local_enabled:
            sources.append(SourceInfo(
                source_type="local",
                description="Local filesystem path",
                example="/path/to/file.pdf",
            ))
        if self._config.ingestion_url_enabled:
            sources.append(SourceInfo(
                source_type="url",
                description="HTTP/HTTPS URL",
                example="https://example.com/document.pdf",
            ))
        if self._config.ingestion_s3_enabled:
            sources.append(SourceInfo(
                source_type="s3",
                description="Amazon S3 URI",
                example="s3://bucket-name/path/to/file.pdf",
            ))
        if self._config.ingestion_azure_enabled:
            sources.append(SourceInfo(
                source_type="azure_blob",
                description="Azure Blob Storage URI",
                example="https://account.blob.core.windows.net/container/file.pdf",
            ))
        if self._config.ingestion_gcs_enabled:
            sources.append(SourceInfo(
                source_type="gcs",
                description="Google Cloud Storage URI",
                example="gs://bucket-name/path/to/file.pdf",
            ))
        return sources
