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

"""Processing result domain models.

:class:`DocumentResult` holds the outcome for a single detected document
(classification, extraction, validation).  :class:`ProcessingResult`
aggregates all document results for a job together with summary statistics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.results.domain.processing_job import ProcessingJob
from fireflyframework_intellidoc.types import (
    DocumentConfidence,
    ValidatorSeverity,
)


class ValidationResult(BaseModel):
    """Result of a single validation check."""

    validator_id: UUID
    validator_code: str
    validator_name: str = ""

    passed: bool
    severity: ValidatorSeverity
    message: str = ""
    field_name: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None

    details: dict[str, Any] = Field(default_factory=dict)


class DocumentResult(BaseModel):
    """Processing result for a single detected document."""

    id: UUID = Field(default_factory=uuid4)
    job_id: UUID

    # Classification
    document_type_id: UUID | None = None
    document_type_code: str | None = None
    classification_confidence: float = 0.0
    classification_reasoning: str = ""
    alternative_classifications: list[dict[str, Any]] = Field(default_factory=list)

    # Pages
    page_range_start: int = 1
    page_range_end: int = 1
    page_count: int = 1

    # Extraction
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    extraction_confidence: dict[str, float] = Field(default_factory=dict)
    extraction_metadata: dict[str, Any] = Field(default_factory=dict)

    # Validation
    validation_results: list[ValidationResult] = Field(default_factory=list)
    is_valid: bool = True
    validation_score: float = 1.0

    # Quality
    overall_confidence: DocumentConfidence = DocumentConfidence.HIGH
    quality_score: float = 1.0

    # Storage
    stored_document_ref: str = ""
    stored_pages_refs: list[str] = Field(default_factory=list)

    # Timing
    processing_duration_ms: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0

    created_at: datetime = Field(default_factory=datetime.now)


class ProcessingResult(BaseModel):
    """Complete processing result for a job."""

    job: ProcessingJob
    documents: list[DocumentResult] = Field(default_factory=list)

    # Summary
    total_fields_extracted: int = 0
    total_validations_passed: int = 0
    total_validations_failed: int = 0
    total_validations_warned: int = 0
    overall_confidence: DocumentConfidence = DocumentConfidence.HIGH

    # Processing metadata
    pipeline_trace_id: str = ""
    model_used: str = ""
    pipeline_version: str = ""
