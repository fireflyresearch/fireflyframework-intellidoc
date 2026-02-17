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

"""Visual validators — VLM-powered visual element verification.

Checks for the presence of visual elements such as signatures,
stamps, photos, and watermarks using a vision-language model.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorType

logger = logging.getLogger(__name__)


class VisualCheckOutput(BaseModel):
    """Structured output from the visual validation VLM."""

    present: bool
    confidence: float = Field(ge=0.0, le=1.0)
    location: str = ""
    details: str = ""


class VisualValidator:
    """VLM-powered visual element validator."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config
        self._agent: Any = None

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.VISUAL

    async def validate(
        self,
        data: dict[str, Any],
        definition: ValidatorDefinition,
        *,
        pages: list[PageImage] | None = None,
    ) -> ValidationResult:
        if not pages:
            return ValidationResult(
                validator_id=definition.id,
                validator_code=definition.code,
                validator_name=definition.name,
                passed=False,
                severity=definition.severity,
                message="No page images available for visual validation",
            )

        prompt = definition.visual_prompt or definition.description
        expected = definition.visual_expected or "present"

        try:
            agent = self._get_agent()
            full_prompt = (
                f"Visual validation check: {prompt}\n\n"
                f"Expected: {expected}\n\n"
                "Examine the document image and determine if the "
                "requested visual element is present."
            )

            result = await agent.run(
                full_prompt,
                output_type=VisualCheckOutput,
            )
            output: VisualCheckOutput = result.output

            if output.present:
                return ValidationResult(
                    validator_id=definition.id,
                    validator_code=definition.code,
                    validator_name=definition.name,
                    passed=True,
                    severity=definition.severity,
                    message=f"Visual element found: {output.location}",
                    details={
                        "confidence": output.confidence,
                        "location": output.location,
                        "details": output.details,
                    },
                )
            else:
                return ValidationResult(
                    validator_id=definition.id,
                    validator_code=definition.code,
                    validator_name=definition.name,
                    passed=False,
                    severity=definition.severity,
                    message=f"Visual element not found: {prompt}",
                    details={
                        "confidence": output.confidence,
                        "details": output.details,
                    },
                )
        except Exception as exc:
            logger.error("Visual validation failed: %s", exc)
            return ValidationResult(
                validator_id=definition.id,
                validator_code=definition.code,
                validator_name=definition.name,
                passed=False,
                severity=definition.severity,
                message=f"Visual validation error: {exc}",
            )

    def _get_agent(self) -> Any:
        if self._agent is None:
            from fireflyframework_genai.agents.base import FireflyAgent

            self._agent = FireflyAgent(
                name="intellidoc-visual-validator",
                model=self._config.get_model("validation"),
                instructions=(
                    "You are a document visual validation agent.\n"
                    "Examine document images and verify the presence "
                    "of requested visual elements.\n"
                    "Report whether the element is present, your "
                    "confidence level, and its location."
                ),
                output_type=VisualCheckOutput,
                description="Validates visual elements in documents",
                tags=["intellidoc", "validator", "vlm"],
            )
        return self._agent
