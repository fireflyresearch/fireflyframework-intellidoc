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

"""Request/Response DTOs for the Operational APIs.

These Pydantic models define the API contract for document processing
submission, job tracking, result retrieval, and analytics endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.types import (
    DocumentConfidence,
    FieldType,
    JobStatus,
    ValidatorSeverity,
)

# ── Target Schema DTOs ────────────────────────────────────────────────


class InlineFieldDefinition(BaseModel):
    """Ad-hoc field definition for one-off extractions not in the catalog."""

    name: str
    display_name: str
    field_type: FieldType
    description: str = ""
    required: bool = False
    location_hint: str = ""


class TargetSchema(BaseModel):
    """Runtime-configurable extraction schema passed in a process request.

    Users can reference catalog fields by code and/or supply inline
    ad-hoc field definitions for one-off extractions.
    """

    field_codes: list[str] = Field(default_factory=list)
    inline_fields: list[InlineFieldDefinition] = Field(default_factory=list)
    extraction_strategy: str = "single_pass"


# ── Processing Submission DTOs ────────────────────────────────────────


class ProcessRequest(BaseModel):
    """Submit a document for processing via source reference."""

    source_type: str = Field(
        description="Source type: 'local', 'url', 's3', 'azure_blob', 'gcs'"
    )
    source_reference: str = Field(
        description="Path, URL, or URI to the source file"
    )
    filename: str = Field(description="Original filename")

    expected_type: str | None = Field(
        default=None,
        description="Expected document type code (skips classification)",
    )
    expected_nature: str | None = Field(
        default=None,
        description="Expected document nature (narrows classification)",
    )
    splitting_strategy: str | None = Field(
        default=None,
        description="Splitting strategy override: 'page_based', 'visual'",
    )
    target_schema: TargetSchema | None = Field(
        default=None,
        description="Override extraction fields; if omitted, uses document type defaults",
    )

    tenant_id: str | None = None
    correlation_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    async_mode: bool = Field(
        default=False,
        description="If true, returns immediately with job ID for polling",
    )


class BatchProcessRequest(BaseModel):
    """Submit multiple documents for processing."""

    items: list[ProcessRequest] = Field(
        min_length=1,
        max_length=100,
        description="List of documents to process",
    )
    stop_on_failure: bool = Field(
        default=False,
        description="Stop processing remaining items on first failure",
    )


class ProcessResponse(BaseModel):
    """Response after submitting a document for processing."""

    job_id: UUID
    status: JobStatus
    message: str = ""
    result: ProcessingResultResponse | None = None

    @classmethod
    def accepted(cls, job_id: UUID) -> ProcessResponse:
        return cls(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Processing job accepted. Poll for status.",
        )

    @classmethod
    def completed(
        cls, job_id: UUID, result: ProcessingResultResponse
    ) -> ProcessResponse:
        return cls(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            message="Processing completed.",
            result=result,
        )


class FailedSubmission(BaseModel):
    """Details about a submission that failed to start."""

    index: int
    filename: str
    error_code: str
    error_message: str


class BatchProcessResponse(BaseModel):
    """Response for batch processing submission."""

    total_submitted: int
    jobs: list[ProcessResponse]
    failed_submissions: list[FailedSubmission] = Field(default_factory=list)


# ── Job Tracking DTOs ─────────────────────────────────────────────────


class JobResponse(BaseModel):
    """Full job details response."""

    id: UUID
    source_type: str
    source_reference: str
    original_filename: str
    file_size_bytes: int
    mime_type: str

    status: JobStatus
    current_step: str
    progress_percent: float

    total_pages: int
    total_documents_detected: int
    documents_processed: int
    documents_succeeded: int
    documents_failed: int

    started_at: datetime | None
    completed_at: datetime | None
    processing_duration_ms: int

    total_tokens_used: int
    total_cost_usd: float

    error_message: str | None
    error_details: dict[str, Any]

    tenant_id: str | None
    correlation_id: str | None
    tags: dict[str, str]

    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, job: Any) -> JobResponse:
        return cls(
            id=job.id,
            source_type=job.source_type,
            source_reference=job.source_reference,
            original_filename=job.original_filename,
            file_size_bytes=job.file_size_bytes,
            mime_type=job.mime_type,
            status=job.status,
            current_step=job.current_step,
            progress_percent=job.progress_percent,
            total_pages=job.total_pages,
            total_documents_detected=job.total_documents_detected,
            documents_processed=job.documents_processed,
            documents_succeeded=job.documents_succeeded,
            documents_failed=job.documents_failed,
            started_at=job.started_at,
            completed_at=job.completed_at,
            processing_duration_ms=job.processing_duration_ms,
            total_tokens_used=job.total_tokens_used,
            total_cost_usd=job.total_cost_usd,
            error_message=job.error_message,
            error_details=job.error_details,
            tenant_id=job.tenant_id,
            correlation_id=job.correlation_id,
            tags=job.tags,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class JobStatusResponse(BaseModel):
    """Lightweight status-only response for polling."""

    job_id: UUID
    status: JobStatus
    current_step: str
    progress_percent: float
    documents_processed: int
    documents_succeeded: int
    documents_failed: int
    total_documents_detected: int
    error_message: str | None = None

    @classmethod
    def from_domain(cls, job: Any) -> JobStatusResponse:
        return cls(
            job_id=job.id,
            status=job.status,
            current_step=job.current_step,
            progress_percent=job.progress_percent,
            documents_processed=job.documents_processed,
            documents_succeeded=job.documents_succeeded,
            documents_failed=job.documents_failed,
            total_documents_detected=job.total_documents_detected,
            error_message=job.error_message,
        )


# ── Result DTOs ───────────────────────────────────────────────────────


class ValidationResultResponse(BaseModel):
    """Single validation check result."""

    validator_id: UUID
    validator_code: str
    validator_name: str
    passed: bool
    severity: ValidatorSeverity
    message: str
    field_name: str | None
    expected_value: str | None
    actual_value: str | None
    details: dict[str, Any]


class DocumentResultResponse(BaseModel):
    """Processing result for a single detected document."""

    id: UUID
    job_id: UUID

    document_type_id: UUID | None
    document_type_code: str | None
    classification_confidence: float
    classification_reasoning: str
    alternative_classifications: list[dict[str, Any]]

    page_range_start: int
    page_range_end: int
    page_count: int

    extracted_fields: dict[str, Any]
    extraction_confidence: dict[str, float]

    validation_results: list[ValidationResultResponse]
    is_valid: bool
    validation_score: float

    overall_confidence: DocumentConfidence
    quality_score: float

    tokens_used: int
    cost_usd: float

    created_at: datetime

    @classmethod
    def from_domain(cls, doc: Any) -> DocumentResultResponse:
        return cls(
            id=doc.id,
            job_id=doc.job_id,
            document_type_id=doc.document_type_id,
            document_type_code=doc.document_type_code,
            classification_confidence=doc.classification_confidence,
            classification_reasoning=doc.classification_reasoning,
            alternative_classifications=doc.alternative_classifications,
            page_range_start=doc.page_range_start,
            page_range_end=doc.page_range_end,
            page_count=doc.page_count,
            extracted_fields=doc.extracted_fields,
            extraction_confidence=doc.extraction_confidence,
            validation_results=[
                ValidationResultResponse(
                    validator_id=v.validator_id,
                    validator_code=v.validator_code,
                    validator_name=v.validator_name,
                    passed=v.passed,
                    severity=v.severity,
                    message=v.message,
                    field_name=v.field_name,
                    expected_value=v.expected_value,
                    actual_value=v.actual_value,
                    details=v.details,
                )
                for v in doc.validation_results
            ],
            is_valid=doc.is_valid,
            validation_score=doc.validation_score,
            overall_confidence=doc.overall_confidence,
            quality_score=doc.quality_score,
            tokens_used=doc.tokens_used,
            cost_usd=doc.cost_usd,
            created_at=doc.created_at,
        )


class ProcessingResultResponse(BaseModel):
    """Complete processing result for a job."""

    job: JobResponse
    documents: list[DocumentResultResponse]

    total_fields_extracted: int
    total_validations_passed: int
    total_validations_failed: int
    overall_confidence: DocumentConfidence

    @classmethod
    def from_domain(cls, result: Any) -> ProcessingResultResponse:
        return cls(
            job=JobResponse.from_domain(result.job),
            documents=[
                DocumentResultResponse.from_domain(d) for d in result.documents
            ],
            total_fields_extracted=result.total_fields_extracted,
            total_validations_passed=result.total_validations_passed,
            total_validations_failed=result.total_validations_failed,
            overall_confidence=result.overall_confidence,
        )


# ── Analytics DTOs ────────────────────────────────────────────────────


class AnalyticsSummaryResponse(BaseModel):
    """Aggregated analytics data."""

    period_start: datetime | None = None
    period_end: datetime | None = None

    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    partially_completed_jobs: int = 0

    total_documents_processed: int = 0
    total_pages_processed: int = 0
    total_fields_extracted: int = 0

    average_processing_time_ms: float = 0.0
    median_processing_time_ms: float = 0.0

    total_tokens_used: int = 0
    total_cost_usd: float = 0.0

    top_document_types: list[DocumentTypeStats] = Field(default_factory=list)
    validation_pass_rate: float = 0.0
    average_confidence: float = 0.0


class DocumentTypeStats(BaseModel):
    """Per-document-type analytics."""

    document_type_code: str
    document_type_name: str
    count: int
    average_confidence: float
    average_processing_time_ms: float
