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

"""Pipeline step: result persistence."""

from __future__ import annotations

import logging
from typing import Any

from pyfly.container.stereotypes import component

from fireflyframework_intellidoc.pipeline.context import IDPPipelineContext
from fireflyframework_intellidoc.results.domain.processing_result import (
    DocumentResult,
)
from fireflyframework_intellidoc.results.ports.outbound import ResultStoragePort
from fireflyframework_intellidoc.types import DocumentConfidence
from fireflyframework_intellidoc.validation.service import ValidationService

logger = logging.getLogger(__name__)


@component
class PersistenceStep:
    """Builds and persists DocumentResult from pipeline context."""

    def __init__(self, result_storage: ResultStoragePort) -> None:
        self._storage = result_storage

    async def execute(
        self, context: IDPPipelineContext, inputs: dict[str, Any]
    ) -> None:
        if context.job_id is None:
            return

        classification = context.classification_result
        extraction = context.extraction_result

        doc_result = DocumentResult(
            job_id=context.job_id,
            page_range_start=context.current_pages[0].page_number
            if context.current_pages
            else 1,
            page_range_end=context.current_pages[-1].page_number
            if context.current_pages
            else 1,
            page_count=len(context.current_pages),
        )

        if classification and classification.best_match:
            doc_result.document_type_id = (
                classification.best_match.document_type_id
            )
            doc_result.document_type_code = (
                classification.best_match.document_type_code
            )
            doc_result.classification_confidence = (
                classification.best_match.confidence
            )
            doc_result.classification_reasoning = (
                classification.best_match.reasoning
            )
            doc_result.alternative_classifications = [
                {
                    "code": c.document_type_code,
                    "confidence": c.confidence,
                    "reasoning": c.reasoning,
                }
                for c in classification.candidates[1:]
            ]

        if extraction:
            doc_result.extracted_fields = extraction.extracted_fields
            doc_result.extraction_confidence = extraction.confidence
            doc_result.extraction_metadata = extraction.metadata
            doc_result.tokens_used = extraction.tokens_used

        if context.validation_results:
            doc_result.validation_results = context.validation_results
            doc_result.is_valid = ValidationService.is_valid(
                context.validation_results
            )
            doc_result.validation_score = ValidationService.compute_validation_score(
                context.validation_results
            )

        # Compute overall confidence
        scores = []
        if classification and classification.best_match:
            scores.append(classification.best_match.confidence)
        if doc_result.validation_score < 1.0:
            scores.append(doc_result.validation_score)
        avg_score = sum(scores) / len(scores) if scores else 1.0
        doc_result.overall_confidence = DocumentConfidence.from_score(avg_score)

        saved = await self._storage.save_document_result(doc_result)
        context.document_results.append(saved)

        logger.info(
            "Persisted document result %s (type: %s, valid: %s)",
            saved.id,
            saved.document_type_code or "unknown",
            saved.is_valid,
        )
