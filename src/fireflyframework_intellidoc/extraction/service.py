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

"""Extraction application service.

Accepts a list of resolved :class:`CatalogField` definitions and
delegates extraction to the VLM extractor agent.
"""

from __future__ import annotations

import logging

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.catalog.domain.catalog_field import CatalogField
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.extraction.agents.field_extractor import (
    FieldExtractorAgent,
)
from fireflyframework_intellidoc.extraction.models import ExtractionResult
from fireflyframework_intellidoc.types import PageImage

logger = logging.getLogger(__name__)


@service
class ExtractionService:
    """Orchestrates field-driven data extraction."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config
        self._extractor = FieldExtractorAgent(config)

    async def extract(
        self,
        pages: list[PageImage],
        fields: list[CatalogField],
    ) -> ExtractionResult:
        """Extract structured data from document pages.

        Uses the provided field definitions to build the extraction
        prompt and run the VLM extractor agent.
        """
        logger.info(
            "Extracting %d fields from %d pages",
            len(fields),
            len(pages),
        )

        result = await self._extractor.extract(pages, fields)

        # Apply default values for missing optional fields
        for field_def in fields:
            if (
                field_def.code not in result.extracted_fields
                and field_def.default_value is not None
            ):
                result.extracted_fields[field_def.code] = field_def.default_value
                result.confidence[field_def.code] = 1.0

        extracted_count = sum(
            1 for v in result.extracted_fields.values() if v is not None
        )
        logger.info(
            "Extracted %d/%d fields (strategy: %s)",
            extracted_count,
            len(fields),
            result.strategy_used,
        )

        return result
