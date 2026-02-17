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

For small documents (up to ``extraction_single_pass_threshold`` pages),
all pages are sent in a single VLM call.  For larger documents, a
two-pass memory-driven strategy is used:

1. **Comprehension pass** — ALL pages are read in batches; the VLM
   summarises key data points from each batch and findings are
   accumulated in :class:`WorkingMemory`.
2. **Extraction pass** — The accumulated memory context is combined
   with the first page (for format reference) and sent to the VLM
   for final structured extraction.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.catalog.domain.catalog_field import CatalogField
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.extraction.models import ExtractionResult
from fireflyframework_intellidoc.types import PageImage, pages_to_content

logger = logging.getLogger(__name__)


# ── VLM output schemas ────────────────────────────────────────────────


class VLMExtractionOutput(BaseModel):
    """Structured output expected from the VLM extractor."""

    fields: dict[str, Any] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
    notes: str = ""


class VLMComprehensionOutput(BaseModel):
    """Output from a single comprehension batch."""

    findings: str = ""
    relevant_fields: dict[str, Any] = Field(default_factory=dict)


# ── Prompt builders ───────────────────────────────────────────────────


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


def _field_descriptions(fields: list[CatalogField]) -> str:
    return "\n".join(_describe_field(f) for f in fields)


def build_extraction_prompt(
    fields: list[CatalogField],
    strategy: str = "single_pass",
) -> str:
    """Build a field-driven extraction prompt for the single-pass case."""
    return (
        "Extract the following fields from the document page images provided.\n\n"
        "Fields to extract:\n"
        + _field_descriptions(fields)
        + "\n\nRules:\n"
        "- Only extract information explicitly visible in the document\n"
        "- If a field cannot be found, set its value to null\n"
        "- Preserve exact values as they appear (don't reformat)\n"
        "- For tables, extract all rows and columns as a list of objects\n"
        "- For each field, provide a confidence score (0.0-1.0)\n"
        "- Pay attention to field location hints when provided\n"
        "- Look across ALL provided pages to find the requested fields\n\n"
        f"Extraction strategy: {strategy}"
    )


def _build_comprehension_prompt(
    fields: list[CatalogField],
    batch_index: int,
    page_range: str,
) -> str:
    """Build a prompt for a single comprehension batch."""
    return (
        f"You are reading batch {batch_index + 1} of a multi-page document "
        f"(pages {page_range}).\n\n"
        "Your task is to identify and extract ANY information from these pages "
        "that is relevant to the following fields:\n\n"
        + _field_descriptions(fields)
        + "\n\nInstructions:\n"
        "- Report ALL relevant data you find, exactly as it appears\n"
        "- Include page numbers where you found each piece of data\n"
        "- If these pages contain none of the requested information, "
        "say 'No relevant fields found on these pages'\n"
        "- For tables, extract all visible rows\n"
        "- Include any contextual information that helps interpret the data "
        "(headers, titles, section names)\n"
        "- Be thorough — do not skip any relevant content"
    )


def _build_synthesis_prompt(
    fields: list[CatalogField],
    memory_context: str,
) -> str:
    """Build the final extraction prompt using accumulated memory."""
    return (
        "You have reviewed an entire multi-page document across multiple batches. "
        "Below is the accumulated knowledge from ALL pages:\n\n"
        + memory_context
        + "\n\n---\n\n"
        "Now produce the FINAL structured extraction for these fields:\n\n"
        + _field_descriptions(fields)
        + "\n\nRules:\n"
        "- Use the accumulated findings above as your primary source\n"
        "- The first page image is provided for visual format reference\n"
        "- Only include information that was actually found in the document\n"
        "- If a field was not found in any batch, set its value to null\n"
        "- Preserve exact values as they appeared in the document\n"
        "- For tables, merge rows found across different batches\n"
        "- For each field, provide a confidence score (0.0-1.0)\n"
        "- Prefer data from the most specific/authoritative page "
        "(e.g., title page for title, header for vendor name)"
    )


# ── Agent ─────────────────────────────────────────────────────────────


class FieldExtractorAgent:
    """Field-driven VLM extractor with memory-based multi-pass support."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config
        self._extractor_agent: Any = None
        self._comprehension_agent: Any = None

    async def extract(
        self,
        pages: list[PageImage],
        fields: list[CatalogField],
        strategy: str = "single_pass",
    ) -> ExtractionResult:
        """Extract structured data from document pages.

        For documents with up to ``extraction_single_pass_threshold``
        pages, sends all pages in one VLM call.  For larger documents,
        runs a two-pass memory-driven extraction.
        """
        threshold = self._config.extraction_single_pass_threshold

        if len(pages) <= threshold:
            return await self._single_pass(pages, fields, strategy)

        return await self._multi_pass(pages, fields, strategy)

    # ── Single-pass (small documents) ─────────────────────────────────

    async def _single_pass(
        self,
        pages: list[PageImage],
        fields: list[CatalogField],
        strategy: str,
    ) -> ExtractionResult:
        agent = self._get_extractor_agent()
        prompt = build_extraction_prompt(fields, strategy)
        multimodal_prompt = pages_to_content(pages, prompt)

        try:
            result = await agent.run(
                multimodal_prompt,
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
            logger.error("Single-pass extraction failed: %s", exc)
            return ExtractionResult(
                strategy_used=strategy,
                metadata={"error": str(exc)},
            )

    # ── Multi-pass (large documents) ──────────────────────────────────

    async def _multi_pass(
        self,
        pages: list[PageImage],
        fields: list[CatalogField],
        strategy: str,
    ) -> ExtractionResult:
        from fireflyframework_genai.memory import MemoryManager

        memory = MemoryManager()
        batch_size = self._config.extraction_pages_per_batch
        total_tokens = 0

        # ── Pass 1: Comprehension — read ALL pages in batches ─────────

        batches = [
            pages[i : i + batch_size]
            for i in range(0, len(pages), batch_size)
        ]

        logger.info(
            "Multi-pass extraction: %d pages in %d batches (batch_size=%d)",
            len(pages),
            len(batches),
            batch_size,
        )

        comprehension_agent = self._get_comprehension_agent()

        for batch_idx, batch in enumerate(batches):
            page_range = f"{batch[0].page_number}-{batch[-1].page_number}"

            prompt = _build_comprehension_prompt(fields, batch_idx, page_range)
            multimodal_prompt = pages_to_content(batch, prompt)

            try:
                result = await comprehension_agent.run(
                    multimodal_prompt,
                    output_type=VLMComprehensionOutput,
                )
                output: VLMComprehensionOutput = result.output
                total_tokens += getattr(result, "usage_tokens", 0)

                # Store findings in working memory
                memory.set_fact(
                    f"batch_{batch_idx}_pages_{page_range}",
                    output.findings,
                )

                # Store any partially extracted field values
                if output.relevant_fields:
                    memory.set_fact(
                        f"batch_{batch_idx}_fields",
                        output.relevant_fields,
                    )

                logger.info(
                    "Comprehension batch %d/%d (pages %s): processed",
                    batch_idx + 1,
                    len(batches),
                    page_range,
                )
            except Exception as exc:
                logger.warning(
                    "Comprehension batch %d failed (pages %s): %s",
                    batch_idx + 1,
                    page_range,
                    exc,
                )
                memory.set_fact(
                    f"batch_{batch_idx}_pages_{page_range}",
                    f"(batch failed: {exc})",
                )

        # ── Pass 2: Extraction — synthesise from memory ───────────────

        memory_context = memory.get_working_context()
        synthesis_prompt = _build_synthesis_prompt(fields, memory_context)

        # Include the first page for visual format reference
        reference_pages = pages[:1]
        multimodal_prompt = pages_to_content(reference_pages, synthesis_prompt)

        try:
            extractor_agent = self._get_extractor_agent()
            result = await extractor_agent.run(
                multimodal_prompt,
                output_type=VLMExtractionOutput,
            )
            final: VLMExtractionOutput = result.output
            total_tokens += getattr(result, "usage_tokens", 0)

            return ExtractionResult(
                extracted_fields=final.fields,
                confidence=final.confidence,
                strategy_used="multi_pass",
                tokens_used=total_tokens,
                metadata={
                    "notes": final.notes,
                    "batches": len(batches),
                    "pages_processed": len(pages),
                } if final.notes else {
                    "batches": len(batches),
                    "pages_processed": len(pages),
                },
            )
        except Exception as exc:
            logger.error("Multi-pass synthesis failed: %s", exc)
            return ExtractionResult(
                strategy_used="multi_pass",
                tokens_used=total_tokens,
                metadata={
                    "error": str(exc),
                    "batches": len(batches),
                    "pages_processed": len(pages),
                },
            )

    # ── Agent creation ────────────────────────────────────────────────

    def _get_extractor_agent(self) -> Any:
        if self._extractor_agent is None:
            from fireflyframework_genai.agents.base import FireflyAgent

            self._extractor_agent = FireflyAgent(
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
        return self._extractor_agent

    def _get_comprehension_agent(self) -> Any:
        if self._comprehension_agent is None:
            from fireflyframework_genai.agents.base import FireflyAgent

            self._comprehension_agent = FireflyAgent(
                name="intellidoc-comprehension",
                model=self._config.get_model("extraction"),
                instructions=(
                    "You are a document comprehension agent.\n"
                    "Your role is to carefully read document pages and identify "
                    "all information relevant to a set of requested fields.\n"
                    "Be thorough — report everything you find, with page numbers.\n"
                    "Preserve exact values as they appear in the document.\n"
                    "If a page contains no relevant information, say so explicitly."
                ),
                output_type=VLMComprehensionOutput,
                description="Reads document pages and identifies relevant data",
                tags=["intellidoc", "comprehension", "vlm"],
            )
        return self._comprehension_agent
