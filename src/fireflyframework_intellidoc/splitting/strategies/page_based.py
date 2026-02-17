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

"""Page-based splitting strategy.

Treats each page as an individual document.  Suitable for
single-page documents such as receipts, certificates, or ID cards.
"""

from __future__ import annotations

from typing import Any

from fireflyframework_intellidoc.splitting.models import SplittingResult
from fireflyframework_intellidoc.types import DocumentBoundary, PageImage


class PageBasedSplitter:
    """Treats every page as a separate document."""

    @property
    def strategy_name(self) -> str:
        return "page_based"

    async def detect_boundaries(
        self,
        pages: list[PageImage],
        **kwargs: Any,
    ) -> SplittingResult:
        boundaries = [
            DocumentBoundary(
                start_page=page.page_number,
                end_page=page.page_number,
                confidence=1.0,
                reasoning="Single page per document (page-based strategy)",
            )
            for page in pages
        ]
        return SplittingResult(
            boundaries=boundaries,
            total_documents_detected=len(boundaries),
            total_pages=len(pages),
            strategy_used="page_based",
            confidence=1.0,
        )
