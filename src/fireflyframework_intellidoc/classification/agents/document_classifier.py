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

"""VLM-powered document classifier agent.

Builds a catalog-driven classification prompt from active document
types and uses a :class:`FireflyAgent` to classify document images.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.catalog.domain.document_type import DocumentType
from fireflyframework_intellidoc.classification.models import (
    ClassificationCandidate,
    ClassificationResult,
)
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.types import DocumentNature, PageImage

logger = logging.getLogger(__name__)


class VLMClassificationOutput(BaseModel):
    """Structured output expected from the VLM classifier."""

    document_type_code: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    nature: str = ""
    alternatives: list[dict[str, Any]] = Field(default_factory=list)


def build_classification_prompt(
    document_types: list[DocumentType],
    *,
    expected_type: str | None = None,
    expected_nature: DocumentNature | None = None,
) -> str:
    """Build a catalog-driven classification prompt."""
    type_descriptions: list[str] = []
    for dt in document_types:
        entry = (
            f"- Code: {dt.code}\n"
            f"  Name: {dt.name}\n"
            f"  Nature: {dt.nature.value}\n"
            f"  Description: {dt.description}\n"
        )
        if dt.visual_description:
            entry += f"  Visual: {dt.visual_description}\n"
        if dt.visual_cues:
            entry += f"  Cues: {', '.join(dt.visual_cues)}\n"
        if dt.sample_keywords:
            entry += f"  Keywords: {', '.join(dt.sample_keywords)}\n"
        if dt.classification_instructions:
            entry += f"  Instructions: {dt.classification_instructions}\n"
        type_descriptions.append(entry)

    prompt = (
        "Classify this document into one of the following registered types:\n\n"
        + "\n".join(type_descriptions)
        + "\n\nAnalyze the document image carefully. Consider:\n"
        "- Visual layout and structure\n"
        "- Logos, headers, footers, and formatting\n"
        "- Key text content and keywords\n"
        "- Document nature and purpose\n\n"
        "Return the best matching document type code, your confidence "
        "(0.0-1.0), and reasoning."
    )

    if expected_type:
        prompt += f"\n\nHint: The expected document type is '{expected_type}'."
    if expected_nature:
        prompt += f"\n\nHint: The expected nature is '{expected_nature.value}'."

    return prompt


class DocumentClassifierAgent:
    """Catalog-driven VLM document classifier."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config
        self._agent: Any = None

    async def classify(
        self,
        pages: list[PageImage],
        available_types: list[DocumentType],
        *,
        expected_type: str | None = None,
        expected_nature: DocumentNature | None = None,
    ) -> ClassificationResult:
        """Classify document pages against available types."""
        if not available_types:
            return ClassificationResult(
                confidence=0.0,
                reasoning="No document types available in catalog",
            )

        agent = self._get_agent()
        prompt = build_classification_prompt(
            available_types,
            expected_type=expected_type,
            expected_nature=expected_nature,
        )

        try:
            result = await agent.run(
                prompt,
                output_type=VLMClassificationOutput,
            )
            output: VLMClassificationOutput = result.output

            # Match output to catalog
            type_map = {dt.code: dt for dt in available_types}
            matched = type_map.get(output.document_type_code)

            best_match = None
            if matched:
                best_match = ClassificationCandidate(
                    document_type_id=matched.id,
                    document_type_code=matched.code,
                    confidence=output.confidence,
                    reasoning=output.reasoning,
                )

            # Build alternative candidates
            candidates = []
            if best_match:
                candidates.append(best_match)
            for alt in output.alternatives:
                alt_code = alt.get("code", "")
                alt_matched = type_map.get(alt_code)
                if alt_matched:
                    candidates.append(
                        ClassificationCandidate(
                            document_type_id=alt_matched.id,
                            document_type_code=alt_matched.code,
                            confidence=alt.get("confidence", 0.0),
                            reasoning=alt.get("reasoning", ""),
                        )
                    )

            return ClassificationResult(
                best_match=best_match,
                candidates=candidates,
                confidence=output.confidence,
                reasoning=output.reasoning,
            )
        except Exception as exc:
            logger.error("Classification failed: %s", exc)
            return ClassificationResult(
                confidence=0.0,
                reasoning=f"Classification failed: {exc}",
            )

    def _get_agent(self) -> Any:
        if self._agent is None:
            from fireflyframework_genai.agents.base import FireflyAgent

            self._agent = FireflyAgent(
                name="intellidoc-classifier",
                model=self._config.get_model("classification"),
                instructions=(
                    "You are an expert document classification agent.\n"
                    "Analyze document images and classify them into one of "
                    "the registered document types.\n"
                    "Consider visual layout, logos, headers, formatting, "
                    "key text, and document purpose.\n"
                    "Return the document type code, confidence, and reasoning."
                ),
                output_type=VLMClassificationOutput,
                description="Classifies documents using the catalog",
                tags=["intellidoc", "classifier", "vlm"],
            )
        return self._agent
