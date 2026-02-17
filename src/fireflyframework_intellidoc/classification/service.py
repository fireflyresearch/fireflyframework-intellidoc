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

Loads active document types from the catalog and delegates
classification to the VLM classifier agent.
"""

from __future__ import annotations

import logging

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.catalog.ports.outbound import (
    DocumentTypeCatalogPort,
)
from fireflyframework_intellidoc.classification.agents.document_classifier import (
    DocumentClassifierAgent,
)
from fireflyframework_intellidoc.classification.models import ClassificationResult
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.exceptions import (
    ClassificationConfidenceTooLowException,
)
from fireflyframework_intellidoc.types import DocumentNature, PageImage

logger = logging.getLogger(__name__)


@service
class ClassificationService:
    """Orchestrates document classification against the catalog."""

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
    ) -> ClassificationResult:
        """Classify document pages against all active catalog types.

        Raises :class:`ClassificationConfidenceTooLowException` when
        the best match confidence falls below the configured threshold.
        """
        active_types = await self._doc_types.find_all_active()

        if expected_nature:
            active_types = [
                dt for dt in active_types if dt.nature == expected_nature
            ]

        result = await self._classifier.classify(
            pages,
            active_types,
            expected_type=expected_type,
            expected_nature=expected_nature,
        )

        # Check confidence threshold
        if result.best_match:
            threshold = self._config.default_confidence_threshold
            # Use document-type-specific threshold if available
            for dt in active_types:
                if dt.code == result.best_match.document_type_code:
                    threshold = dt.classification_confidence_threshold
                    break

            if result.best_match.confidence < threshold:
                raise ClassificationConfidenceTooLowException(
                    result.best_match.confidence, threshold
                )

        logger.info(
            "Classified document as '%s' (confidence: %.2f)",
            result.best_match.document_type_code if result.best_match else "unknown",
            result.confidence,
        )
        return result
