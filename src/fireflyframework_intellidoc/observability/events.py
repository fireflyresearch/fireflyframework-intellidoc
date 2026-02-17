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

"""Domain events for the IDP pipeline.

These events are published at key points in the processing lifecycle
and can be consumed by listeners for observability, webhooks, or
audit logging.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.types import DocumentConfidence, JobStatus


class IntelliDocEvent(BaseModel):
    """Base event for all IntelliDoc domain events."""

    event_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: str | None = None
    tenant_id: str | None = None


class JobCreatedEvent(IntelliDocEvent):
    """Published when a new processing job is created."""

    event_type: str = "intellidoc.job.created"
    job_id: UUID
    source_type: str
    filename: str


class JobStartedEvent(IntelliDocEvent):
    """Published when a job begins processing."""

    event_type: str = "intellidoc.job.started"
    job_id: UUID


class JobCompletedEvent(IntelliDocEvent):
    """Published when a job completes (success or partial)."""

    event_type: str = "intellidoc.job.completed"
    job_id: UUID
    status: JobStatus
    documents_succeeded: int
    documents_failed: int
    processing_duration_ms: int
    total_tokens_used: int
    total_cost_usd: float


class JobFailedEvent(IntelliDocEvent):
    """Published when a job fails entirely."""

    event_type: str = "intellidoc.job.failed"
    job_id: UUID
    error_code: str
    error_message: str
    processing_duration_ms: int


class DocumentClassifiedEvent(IntelliDocEvent):
    """Published when a document within a job is classified."""

    event_type: str = "intellidoc.document.classified"
    job_id: UUID
    document_index: int
    document_type_code: str | None
    confidence: float
    page_range_start: int
    page_range_end: int


class DocumentExtractedEvent(IntelliDocEvent):
    """Published when data extraction completes for a document."""

    event_type: str = "intellidoc.document.extracted"
    job_id: UUID
    document_index: int
    fields_extracted: int
    tokens_used: int


class DocumentValidatedEvent(IntelliDocEvent):
    """Published when validation completes for a document."""

    event_type: str = "intellidoc.document.validated"
    job_id: UUID
    document_index: int
    is_valid: bool
    validations_passed: int
    validations_failed: int
    validation_score: float


class DocumentProcessedEvent(IntelliDocEvent):
    """Published when a single document is fully processed."""

    event_type: str = "intellidoc.document.processed"
    job_id: UUID
    document_id: UUID
    document_type_code: str | None
    overall_confidence: DocumentConfidence
    is_valid: bool
    processing_duration_ms: int
