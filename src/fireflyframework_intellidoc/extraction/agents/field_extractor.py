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

"""VLM-powered field-driven extractor agent.

Dynamically builds extraction prompts from :class:`CatalogField`
definitions and uses a :class:`FireflyAgent` to extract structured
data from document images.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.catalog.domain.catalog_field import CatalogField
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.extraction.models import ExtractionResult
from fireflyframework_intellidoc.types import PageImage

logger = logging.getLogger(__name__)


class VLMExtractionOutput(BaseModel):
    """Structured output expected from the VLM extractor."""

    fields: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
    notes: str = ""


def build_extraction_prompt(
    fields: list[CatalogField],
    strategy: str = "single_pass",
) -> str:
    """Build a field-driven extraction prompt."""
    field_descriptions: list[str] = []
    for f in fields:
        desc = _describe_field(f)
        field_descriptions.append(desc)

    prompt = (
        "Extract the following fields from this document image.\n\n"
        "Fields to extract:\n"
        + "\n".join(field_descriptions)
        + "\n\nRules:\n"
        "- Only extract information explicitly visible in the document\n"
        "- If a field cannot be found, set its value to null\n"
        "- Preserve exact values as they appear (don't reformat)\n"
        "- For tables, extract all rows and columns as a list of objects\n"
        "- For each field, provide a confidence score (0.0-1.0)\n"
        "- Pay attention to field location hints when provided\n\n"
        f"Extraction strategy: {strategy}"
    )
    return prompt


def _describe_field(field: CatalogField, indent: int = 0) -> str:
    """Generate a human-readable description of a field for the VLM."""
    prefix = "  " * indent
    parts = [
        f"{prefix}- {field.code} ({field.field_type.value}): "
        f"{field.display_name}"
    ]

    if field.description:
        parts.append(f"{prefix}  Description: {field.description}")
    if field.required:
        parts.append(f"{prefix}  Required: yes")
    if field.location_hint:
        parts.append(f"{prefix}  Location: {field.location_hint}")
    if field.format_pattern:
        parts.append(f"{prefix}  Format: {field.format_pattern}")
    if field.allowed_values:
        parts.append(
            f"{prefix}  Allowed values: {', '.join(field.allowed_values)}"
        )
    if field.min_value is not None or field.max_value is not None:
        range_str = f"{field.min_value or '...'} to {field.max_value or '...'}"
        parts.append(f"{prefix}  Range: {range_str}")
    if field.table_columns:
        parts.append(f"{prefix}  Table columns:")
        for col in field.table_columns:
            parts.append(_describe_field(col, indent + 2))

    return "\n".join(parts)


class FieldExtractorAgent:
    """Field-driven VLM extractor."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config
        self._agent: Any = None

    async def extract(
        self,
        pages: list[PageImage],
        fields: list[CatalogField],
        strategy: str = "single_pass",
    ) -> ExtractionResult:
        """Extract structured data from document pages using the fields."""
        agent = self._get_agent()
        prompt = build_extraction_prompt(fields, strategy)

        try:
            result = await agent.run(
                prompt,
                output_type=VLMExtractionOutput,
            )
            output: VLMExtractionOutput = result.output

            return ExtractionResult(
                extracted_fields=output.fields,
                confidence=output.confidence,
                strategy_used=strategy,
                tokens_used=getattr(result, "usage_tokens", 0),
                metadata={"notes": output.notes} if output.notes else {},
            )
        except Exception as exc:
            logger.error("Extraction failed: %s", exc)
            return ExtractionResult(
                strategy_used=strategy,
                metadata={"error": str(exc)},
            )

    def _get_agent(self) -> Any:
        if self._agent is None:
            from fireflyframework_genai.agents.base import FireflyAgent

            self._agent = FireflyAgent(
                name="intellidoc-extractor",
                model=self._config.get_model("extraction"),
                instructions=(
                    "You are an expert document data extraction agent.\n"
                    "Extract structured information from document images "
                    "according to the provided field definitions.\n"
                    "Only extract information explicitly present in the document.\n"
                    "If a field cannot be found, return null.\n"
                    "Preserve exact values as they appear.\n"
                    "For tables, extract all rows and columns.\n"
                    "Provide confidence scores for each field."
                ),
                output_type=VLMExtractionOutput,
                description="Extracts structured data from documents",
                tags=["intellidoc", "extractor", "vlm"],
            )
        return self._agent
