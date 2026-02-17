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

"""Pipeline step: file ingestion."""

from __future__ import annotations

from typing import Any

from fireflyframework_intellidoc.ingestion.service import IngestionService
from fireflyframework_intellidoc.pipeline.context import IDPPipelineContext


class IngestionStep:
    """Downloads/reads the file from the configured source adapter."""

    def __init__(self, ingestion_service: IngestionService) -> None:
        self._ingestion = ingestion_service

    async def execute(
        self, context: IDPPipelineContext, inputs: dict[str, Any]
    ) -> None:
        file_ref = await self._ingestion.ingest(
            context.source_type, context.source_reference
        )
        context.file_reference = file_ref
