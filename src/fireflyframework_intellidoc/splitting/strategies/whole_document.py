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

"""Whole-document splitting strategy.

Treats all pages as a single document — no boundary detection.
This is the default strategy, suitable for most IDP use cases
where the input file contains a single document (invoice,
contract, report, etc.).
"""

from __future__ import annotations

from typing import Any

from fireflyframework_intellidoc.splitting.models import SplittingResult
from fireflyframework_intellidoc.types import DocumentBoundary, PageImage


class WholeDocumentSplitter:
    """Treats the entire file as one document."""

    @property
    def strategy_name(self) -> str:
        return "whole_document"

    async def detect_boundaries(
        self,
        pages: list[PageImage],
        **kwargs: Any,
    ) -> SplittingResult:
        if not pages:
            return SplittingResult(
                total_documents_detected=0,
                total_pages=0,
                strategy_used="whole_document",
            )

        return SplittingResult(
            boundaries=[
                DocumentBoundary(
                    start_page=pages[0].page_number,
                    end_page=pages[-1].page_number,
                    confidence=1.0,
                    reasoning="Whole document (single document strategy)",
                )
            ],
            total_documents_detected=1,
            total_pages=len(pages),
            strategy_used="whole_document",
            confidence=1.0,
        )
