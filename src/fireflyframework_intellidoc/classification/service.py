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

"""Classification application service.

Gathers document types from all available sources (catalog, ad-hoc,
synthesized) and delegates classification to the VLM classifier agent.
Always returns a :class:`ClassificationResult` — never raises on low
confidence.  The orchestrator decides what to do with the result.
"""

from __future__ import annotations

import logging

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.catalog.domain.document_type import DocumentType
from fireflyframework_intellidoc.catalog.ports.outbound import (
    DocumentTypeCatalogPort,
)
from fireflyframework_intellidoc.classification.agents.document_classifier import (
    DocumentClassifierAgent,
)
from fireflyframework_intellidoc.classification.models import ClassificationResult
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.results.exposure.schemas import (
    AdHocDocumentType,
    ad_hoc_to_document_type,
)
from fireflyframework_intellidoc.types import DocumentNature, PageImage

logger = logging.getLogger(__name__)


@service
class ClassificationService:
    """Classifies documents against all available types."""

    def __init__(
        self,
        config: IntelliDocConfig,
        document_type_port: DocumentTypeCatalogPort,
    ) -> None:
        self._config = config
        self._doc_types = document_type_port
        self._classifier = DocumentClassifierAgent(config)

    async def classify(
        self,
        pages: list[PageImage],
        *,
        expected_type: str | None = None,
        expected_nature: DocumentNature | None = None,
        ad_hoc_types: list[AdHocDocumentType] | None = None,
    ) -> ClassificationResult:
        """Classify document pages against all available types.

        Types are gathered from three sources (merged in order):
        1. Catalog types (from the persistent catalog)
        2. Ad-hoc types (from the runtime request)
        3. Synthesized type (from ``expected_type`` if no others exist)

        Always returns a result.  The caller decides what to do
        with the confidence score.
        """
        # 1. Gather types from all sources
        catalog_types = await self._doc_types.find_all_active()

        if ad_hoc_types:
            runtime_types = [ad_hoc_to_document_type(t) for t in ad_hoc_types]
            all_types = catalog_types + runtime_types
        else:
            all_types = list(catalog_types)

        # 2. Filter by nature
        if expected_nature:
            all_types = [
                dt for dt in all_types if dt.nature == expected_nature
            ]

        # 3. Synthesize for binary classification if no types available
        if not all_types and expected_type:
            all_types = [
                DocumentType(
                    code=expected_type,
                    name=expected_type.replace("_", " ").title(),
                    description="",
                    nature=DocumentNature.OTHER,
                )
            ]

        if not all_types:
            return ClassificationResult(
                confidence=0.0, reasoning="No document types available"
            )

        result = await self._classifier.classify(
            pages,
            all_types,
            expected_type=expected_type,
            expected_nature=expected_nature,
        )

        logger.info(
            "Classified document as '%s' (confidence: %.2f)",
            result.best_match.document_type_code if result.best_match else "unknown",
            result.confidence,
        )
        return result
