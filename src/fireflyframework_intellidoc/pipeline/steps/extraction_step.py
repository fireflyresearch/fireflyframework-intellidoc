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

"""Pipeline step: data extraction."""

from __future__ import annotations

from typing import Any

from pyfly.container.stereotypes import component

from fireflyframework_intellidoc.extraction.service import ExtractionService
from fireflyframework_intellidoc.pipeline.context import IDPPipelineContext


@component
class ExtractionStep:
    """Extracts structured data using the resolved fields."""

    def __init__(self, extraction_service: ExtractionService) -> None:
        self._extraction = extraction_service

    async def execute(
        self, context: IDPPipelineContext, inputs: dict[str, Any]
    ) -> None:
        if not context.resolved_fields:
            return

        result = await self._extraction.extract(
            pages=context.current_pages,
            fields=context.resolved_fields,
        )
        context.extraction_result = result
