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

"""Processing orchestrator.

:class:`ProcessingOrchestrator` manages the complete document
processing lifecycle — creates a job, executes the pipeline steps
in order, handles per-document fan-out, and reports results.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.catalog.service import CatalogService
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.exceptions import PipelineException
from fireflyframework_intellidoc.pipeline.context import IDPPipelineContext
from fireflyframework_intellidoc.pipeline.steps.classification_step import (
    ClassificationStep,
)
from fireflyframework_intellidoc.pipeline.steps.extraction_step import (
    ExtractionStep,
)
from fireflyframework_intellidoc.pipeline.steps.ingestion_step import (
    IngestionStep,
)
from fireflyframework_intellidoc.pipeline.steps.persistence_step import (
    PersistenceStep,
)
from fireflyframework_intellidoc.pipeline.steps.preprocessing_step import (
    PreProcessingStep,
)
from fireflyframework_intellidoc.pipeline.steps.splitting_step import (
    SplittingStep,
)
from fireflyframework_intellidoc.pipeline.steps.validation_step import (
    ValidationStep,
)
from fireflyframework_intellidoc.results.domain.processing_job import (
    ProcessingJob,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ProcessingResult,
)
from fireflyframework_intellidoc.results.exposure.schemas import TargetSchema
from fireflyframework_intellidoc.results.service import ResultService
from fireflyframework_intellidoc.types import JobStatus

logger = logging.getLogger(__name__)


@service
class ProcessingOrchestrator:
    """Orchestrates the complete document processing workflow."""

    def __init__(
        self,
        config: IntelliDocConfig,
        result_service: ResultService,
        catalog_service: CatalogService,
        ingestion_step: IngestionStep,
        preprocessing_step: PreProcessingStep,
        splitting_step: SplittingStep,
        classification_step: ClassificationStep,
        extraction_step: ExtractionStep,
        validation_step: ValidationStep,
        persistence_step: PersistenceStep,
    ) -> None:
        self._config = config
        self._results = result_service
        self._catalog = catalog_service
        self._ingest = ingestion_step
        self._preprocess = preprocessing_step
        self._split = splitting_step
        self._classify = classification_step
        self._extract = extraction_step
        self._validate = validation_step
        self._persist = persistence_step

    async def process(
        self,
        source_type: str,
        source_reference: str,
        *,
        filename: str,
        expected_type: str | None = None,
        expected_nature: str | None = None,
        splitting_strategy: str | None = None,
        target_schema: TargetSchema | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> ProcessingResult:
        """Execute the full IDP pipeline synchronously.

        Creates a processing job, runs all pipeline stages, and
        returns the complete :class:`ProcessingResult`.
        """
        # Create job
        job = await self._results.create_job(
            source_type,
            source_reference,
            filename,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            tags=tags,
        )

        ctx = IDPPipelineContext(
            job_id=job.id,
            source_type=source_type,
            source_reference=source_reference,
            filename=filename,
            expected_type=expected_type,
            expected_nature=expected_nature,
            splitting_strategy=splitting_strategy,
            target_field_codes=target_schema.field_codes if target_schema else None,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            tags=tags or {},
        )

        try:
            await self._run_pipeline(ctx, job)
        except Exception as exc:
            logger.error("Pipeline failed for job %s: %s", job.id, exc)
            await self._results.update_job_status(
                job.id,
                JobStatus.FAILED,
                error_message=str(exc),
            )
            raise PipelineException(
                f"Pipeline failed: {exc}", code="PIPELINE_EXECUTION_ERROR"
            ) from exc

        return await self._results.get_processing_result(job.id)

    async def submit(
        self,
        source_type: str,
        source_reference: str,
        *,
        filename: str,
        expected_type: str | None = None,
        expected_nature: str | None = None,
        splitting_strategy: str | None = None,
        target_schema: TargetSchema | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> UUID:
        """Create a job and schedule pipeline execution in the background.

        Returns the job ID immediately for status polling.
        """
        job = await self._results.create_job(
            source_type,
            source_reference,
            filename,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            tags=tags,
        )

        ctx = IDPPipelineContext(
            job_id=job.id,
            source_type=source_type,
            source_reference=source_reference,
            filename=filename,
            expected_type=expected_type,
            expected_nature=expected_nature,
            splitting_strategy=splitting_strategy,
            target_field_codes=target_schema.field_codes if target_schema else None,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            tags=tags or {},
        )

        asyncio.create_task(self._execute_in_background(ctx, job))
        return job.id

    async def _execute_in_background(
        self,
        ctx: IDPPipelineContext,
        job: ProcessingJob,
    ) -> None:
        """Run the pipeline in the background, updating job status on failure."""
        try:
            await self._run_pipeline(ctx, job)
        except Exception as exc:
            logger.error("Background pipeline failed for job %s: %s", job.id, exc)
            await self._results.update_job_status(
                job.id,
                JobStatus.FAILED,
                error_message=str(exc),
            )

    async def _run_pipeline(
        self,
        ctx: IDPPipelineContext,
        job: ProcessingJob,
    ) -> None:
        """Execute the pipeline stages in sequence."""
        inputs: dict[str, Any] = {}

        # Stage 1: Ingest
        await self._update_status(job, JobStatus.INGESTING, "ingest", 10.0)
        await self._ingest.execute(ctx, inputs)

        # Update job with file info
        if ctx.file_reference:
            job.file_size_bytes = ctx.file_reference.file_size_bytes
            job.mime_type = ctx.file_reference.mime_type

        # Stage 2: Pre-process
        await self._update_status(
            job, JobStatus.PREPROCESSING, "preprocess", 20.0
        )
        await self._preprocess.execute(ctx, inputs)

        if ctx.preprocessing_result:
            job.total_pages = ctx.preprocessing_result.total_pages

        # Stage 3: Split
        await self._update_status(job, JobStatus.SPLITTING, "split", 30.0)
        await self._split.execute(ctx, inputs)

        if ctx.splitting_result:
            job.total_documents_detected = (
                ctx.splitting_result.total_documents_detected
            )

        # Stage 4-7: Per-document processing
        if ctx.splitting_result and ctx.preprocessing_result:
            total_docs = ctx.splitting_result.total_documents_detected
            for i, boundary in enumerate(ctx.splitting_result.boundaries):
                # Set up per-document context
                ctx.current_doc_index = i
                ctx.current_pages = ctx.preprocessing_result.pages[
                    boundary.start_page - 1 : boundary.end_page
                ]
                ctx.classification_result = None
                ctx.extraction_result = None
                ctx.validation_results = []

                doc_progress = 40.0 + (50.0 * i / max(total_docs, 1))

                try:
                    # Classify
                    await self._update_status(
                        job, JobStatus.CLASSIFYING, "classify", doc_progress
                    )
                    await self._classify.execute(ctx, inputs)

                    # Resolve target fields
                    if ctx.target_field_codes:
                        ctx.resolved_fields = await self._catalog.resolve_fields(
                            ctx.target_field_codes
                        )
                    elif (
                        ctx.classification_result
                        and ctx.classification_result.best_match
                    ):
                        ctx.resolved_fields = await self._catalog.get_default_fields(
                            ctx.classification_result.best_match.document_type_id
                        )

                    # Extract
                    await self._update_status(
                        job, JobStatus.EXTRACTING, "extract", doc_progress + 15
                    )
                    await self._extract.execute(ctx, inputs)

                    # Validate
                    await self._update_status(
                        job, JobStatus.VALIDATING, "validate", doc_progress + 30
                    )
                    await self._validate.execute(ctx, inputs)

                    # Persist document result
                    await self._persist.execute(ctx, inputs)

                    job.documents_succeeded += 1
                except Exception as exc:
                    logger.error(
                        "Processing failed for document %d in job %s: %s",
                        i,
                        job.id,
                        exc,
                    )
                    job.documents_failed += 1

                job.documents_processed += 1

        # Final status
        if job.documents_failed > 0 and job.documents_succeeded > 0:
            final_status = JobStatus.PARTIALLY_COMPLETED
        elif job.documents_failed > 0:
            final_status = JobStatus.FAILED
        else:
            final_status = JobStatus.COMPLETED

        await self._update_status(job, final_status, "complete", 100.0)

    async def _update_status(
        self,
        job: ProcessingJob,
        status: JobStatus,
        step: str,
        progress: float,
    ) -> None:
        await self._results.update_job_status(
            job.id,
            status,
            current_step=step,
            progress_percent=min(progress, 100.0),
        )
