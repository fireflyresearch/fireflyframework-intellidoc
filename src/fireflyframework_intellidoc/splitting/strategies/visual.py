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

"""VLM-powered visual document splitting strategy.

Sends consecutive page images to a vision-language model to detect
where one document ends and another begins based on visual cues
such as layout changes, headers, footers, and document structure.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.splitting.models import SplittingResult
from fireflyframework_intellidoc.types import DocumentBoundary, PageImage

logger = logging.getLogger(__name__)


class BoundaryAnalysis(BaseModel):
    """VLM output for boundary detection between two pages."""

    is_boundary: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    detected_type_hint: str = ""


class VisualSplitter:
    """Uses a VLM agent to detect document boundaries visually."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config
        self._agent: Any = None

    @property
    def strategy_name(self) -> str:
        return "visual"

    async def detect_boundaries(
        self,
        pages: list[PageImage],
        **kwargs: Any,
    ) -> SplittingResult:
        if len(pages) <= 1:
            return self._single_document(pages)

        agent = self._get_agent()
        boundaries: list[DocumentBoundary] = []
        current_start = pages[0].page_number

        for i in range(len(pages) - 1):
            current_page = pages[i]
            next_page = pages[i + 1]

            analysis = await self._analyze_boundary(
                agent, current_page, next_page
            )

            if analysis.is_boundary:
                boundaries.append(
                    DocumentBoundary(
                        start_page=current_start,
                        end_page=current_page.page_number,
                        confidence=analysis.confidence,
                        reasoning=analysis.reasoning,
                        detected_type_hint=analysis.detected_type_hint,
                    )
                )
                current_start = next_page.page_number

        # Close the last document
        boundaries.append(
            DocumentBoundary(
                start_page=current_start,
                end_page=pages[-1].page_number,
                confidence=1.0,
                reasoning="Final document segment",
            )
        )

        avg_confidence = (
            sum(b.confidence for b in boundaries) / len(boundaries)
            if boundaries
            else 1.0
        )

        return SplittingResult(
            boundaries=boundaries,
            total_documents_detected=len(boundaries),
            total_pages=len(pages),
            strategy_used="visual",
            confidence=avg_confidence,
        )

    async def _analyze_boundary(
        self,
        agent: Any,
        current_page: PageImage,
        next_page: PageImage,
    ) -> BoundaryAnalysis:
        """Ask the VLM whether there's a document boundary between two pages."""
        try:
            from fireflyframework_genai.agents.base import FireflyAgent

            prompt = (
                "Analyze these two consecutive document pages. "
                "Determine if they belong to the same document or if "
                "the second page starts a new, different document.\n\n"
                "Look for:\n"
                "- Different headers/footers/logos\n"
                "- Change in document layout or style\n"
                "- New document title or heading\n"
                "- Different formatting patterns\n"
                "- Separator pages (blank, barcode, cover)\n\n"
                f"Page {current_page.page_number} → Page {next_page.page_number}"
            )

            result = await agent.run(
                prompt,
                output_type=BoundaryAnalysis,
            )
            return result.output
        except Exception as exc:
            logger.warning(
                "VLM boundary detection failed between pages %d-%d: %s",
                current_page.page_number,
                next_page.page_number,
                exc,
            )
            return BoundaryAnalysis(
                is_boundary=False,
                confidence=0.5,
                reasoning=f"VLM analysis failed: {exc}",
            )

    def _get_agent(self) -> Any:
        if self._agent is None:
            from fireflyframework_genai.agents.base import FireflyAgent

            self._agent = FireflyAgent(
                name="intellidoc-boundary-detector",
                model=self._config.get_model("splitting"),
                instructions=(
                    "You are a document boundary detection agent. "
                    "Analyze consecutive page images to determine "
                    "where one document ends and another begins."
                ),
                output_type=BoundaryAnalysis,
                tags=["intellidoc", "splitter", "vlm"],
            )
        return self._agent

    @staticmethod
    def _single_document(pages: list[PageImage]) -> SplittingResult:
        if not pages:
            return SplittingResult(
                total_documents_detected=0,
                total_pages=0,
                strategy_used="visual",
            )
        return SplittingResult(
            boundaries=[
                DocumentBoundary(
                    start_page=pages[0].page_number,
                    end_page=pages[-1].page_number,
                    confidence=1.0,
                    reasoning="Single page document",
                )
            ],
            total_documents_detected=1,
            total_pages=len(pages),
            strategy_used="visual",
            confidence=1.0,
        )
