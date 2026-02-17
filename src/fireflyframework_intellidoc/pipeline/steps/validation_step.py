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

"""Pipeline step: document validation."""

from __future__ import annotations

from typing import Any

from pyfly.container.stereotypes import component

from fireflyframework_intellidoc.pipeline.context import IDPPipelineContext
from fireflyframework_intellidoc.validation.service import ValidationService


@component
class ValidationStep:
    """Runs validators and field-level rules against extracted data."""

    def __init__(self, validation_service: ValidationService) -> None:
        self._validation = validation_service

    async def execute(
        self, context: IDPPipelineContext, inputs: dict[str, Any]
    ) -> None:
        extraction = context.extraction_result
        if extraction is None:
            return

        classification = context.classification_result
        document_type_id = None
        if classification and classification.best_match:
            document_type_id = classification.best_match.document_type_id

        results = await self._validation.validate(
            pages=context.current_pages,
            extracted_data=extraction.extracted_fields,
            document_type_id=document_type_id,
            resolved_fields=context.resolved_fields or None,
        )
        context.validation_results = results
