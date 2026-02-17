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

"""IDP pipeline context.

:class:`IDPPipelineContext` carries typed state between pipeline steps,
providing each step with structured access to upstream results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from fireflyframework_intellidoc.catalog.domain.catalog_field import CatalogField
from fireflyframework_intellidoc.classification.models import ClassificationResult
from fireflyframework_intellidoc.extraction.models import ExtractionResult
from fireflyframework_intellidoc.preprocessing.models import PreProcessingResult
from fireflyframework_intellidoc.results.domain.processing_result import (
    DocumentResult,
    ValidationResult,
)
from fireflyframework_intellidoc.splitting.models import SplittingResult
from fireflyframework_intellidoc.types import FileReference, PageImage


@dataclass
class IDPPipelineContext:
    """Carries state through the IDP processing pipeline."""

    # Job metadata
    job_id: UUID | None = None
    source_type: str = ""
    source_reference: str = ""
    filename: str = ""
    expected_type: str | None = None
    expected_nature: str | None = None
    tenant_id: str | None = None
    correlation_id: str | None = None
    splitting_strategy: str | None = None
    tags: dict[str, str] = field(default_factory=dict)

    # Target schema (from request)
    target_field_codes: list[str] | None = None
    resolved_fields: list[CatalogField] = field(default_factory=list)

    # Pipeline state (populated by steps)
    file_reference: FileReference | None = None
    preprocessing_result: PreProcessingResult | None = None
    splitting_result: SplittingResult | None = None

    # Per-document results (populated during fan-out)
    current_pages: list[PageImage] = field(default_factory=list)
    current_doc_index: int = 0
    classification_result: ClassificationResult | None = None
    extraction_result: ExtractionResult | None = None
    validation_results: list[ValidationResult] = field(default_factory=list)

    # Aggregated results
    document_results: list[DocumentResult] = field(default_factory=list)

    # Observability
    metadata: dict[str, Any] = field(default_factory=dict)
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
