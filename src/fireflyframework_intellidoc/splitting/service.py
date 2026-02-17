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

"""Splitting application service.

Dispatches document boundary detection to the configured splitting
strategy (page-based, visual, etc.).
"""

from __future__ import annotations

import logging

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.exceptions import SplittingException
from fireflyframework_intellidoc.preprocessing.models import PreProcessingResult
from fireflyframework_intellidoc.splitting.models import SplittingResult
from fireflyframework_intellidoc.splitting.ports.outbound import (
    DocumentSplitterPort,
)

logger = logging.getLogger(__name__)


@service
class SplittingService:
    """Coordinates document splitting using registered strategies."""

    def __init__(
        self,
        config: IntelliDocConfig,
        splitters: list[DocumentSplitterPort],
    ) -> None:
        self._config = config
        self._strategies: dict[str, DocumentSplitterPort] = {}
        for splitter in splitters:
            self._strategies[splitter.strategy_name] = splitter

    async def detect_boundaries(
        self,
        preprocessing_result: PreProcessingResult,
        *,
        strategy: str | None = None,
    ) -> SplittingResult:
        """Detect document boundaries in the preprocessed pages."""
        strategy_name = strategy or self._config.default_splitting_strategy
        splitter = self._strategies.get(strategy_name)

        if splitter is None:
            available = ", ".join(self._strategies.keys()) or "none"
            raise SplittingException(
                f"Unknown splitting strategy '{strategy_name}'. "
                f"Available: {available}",
                code="SPLITTING_UNKNOWN_STRATEGY",
            )

        logger.info(
            "Splitting %d pages using '%s' strategy",
            preprocessing_result.total_pages,
            strategy_name,
        )

        result = await splitter.detect_boundaries(preprocessing_result.pages)

        logger.info(
            "Detected %d documents across %d pages (confidence: %.2f)",
            result.total_documents_detected,
            result.total_pages,
            result.confidence,
        )
        return result

    @property
    def available_strategies(self) -> list[str]:
        return list(self._strategies.keys())
