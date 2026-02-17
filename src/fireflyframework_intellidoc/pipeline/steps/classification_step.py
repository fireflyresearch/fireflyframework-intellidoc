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

"""Pipeline step: document classification."""

from __future__ import annotations

from typing import Any

from fireflyframework_intellidoc.classification.service import (
    ClassificationService,
)
from fireflyframework_intellidoc.pipeline.context import IDPPipelineContext
from fireflyframework_intellidoc.types import DocumentNature


class ClassificationStep:
    """Classifies a document against the catalog."""

    def __init__(
        self, classification_service: ClassificationService
    ) -> None:
        self._classification = classification_service

    async def execute(
        self, context: IDPPipelineContext, inputs: dict[str, Any]
    ) -> None:
        expected_nature = None
        if context.expected_nature:
            try:
                expected_nature = DocumentNature(context.expected_nature)
            except ValueError:
                pass

        result = await self._classification.classify(
            pages=context.current_pages,
            expected_type=context.expected_type,
            expected_nature=expected_nature,
        )
        context.classification_result = result
