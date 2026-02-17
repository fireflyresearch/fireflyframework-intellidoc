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

"""Pipeline step: document splitting."""

from __future__ import annotations

from typing import Any

from fireflyframework_intellidoc.pipeline.context import IDPPipelineContext
from fireflyframework_intellidoc.splitting.service import SplittingService


class SplittingStep:
    """Detects document boundaries in multi-document files."""

    def __init__(self, splitting_service: SplittingService) -> None:
        self._splitting = splitting_service

    async def execute(
        self, context: IDPPipelineContext, inputs: dict[str, Any]
    ) -> None:
        if context.preprocessing_result is None:
            raise ValueError("Preprocessing result not set in context")

        result = await self._splitting.detect_boundaries(
            context.preprocessing_result,
            strategy=context.splitting_strategy,
        )
        context.splitting_result = result
