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

"""Completeness validators — required fields and page count checks."""

from __future__ import annotations

from typing import Any

from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorType


class CompletenessValidator:
    """Validates document completeness (field coverage, page count)."""

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.COMPLETENESS

    async def validate(
        self,
        data: dict[str, Any],
        definition: ValidatorDefinition,
        *,
        pages: list[PageImage] | None = None,
    ) -> ValidationResult:
        config = definition.config

        # Check minimum pages
        min_pages = config.get("min_pages")
        if min_pages is not None and pages is not None:
            if len(pages) < int(min_pages):
                return self._fail(
                    definition,
                    f"Document has {len(pages)} pages, minimum required: {min_pages}",
                    expected_value=str(min_pages),
                    actual_value=str(len(pages)),
                )

        # Check minimum fields percentage
        min_fields_percent = config.get("min_fields_percent")
        if min_fields_percent is not None:
            required_fields = definition.applicable_fields or list(data.keys())
            if required_fields:
                present = sum(
                    1
                    for f in required_fields
                    if data.get(f) is not None and str(data.get(f)).strip()
                )
                percent = (present / len(required_fields)) * 100
                if percent < float(min_fields_percent):
                    return self._fail(
                        definition,
                        f"Field completeness {percent:.1f}% below "
                        f"minimum {min_fields_percent}%",
                        expected_value=f">= {min_fields_percent}%",
                        actual_value=f"{percent:.1f}%",
                    )

        # Check specific required fields
        required_fields = config.get("required_fields", [])
        missing = [
            f for f in required_fields
            if data.get(f) is None or not str(data.get(f)).strip()
        ]
        if missing:
            return self._fail(
                definition,
                f"Missing required fields: {', '.join(missing)}",
            )

        return self._pass(definition, "Document completeness check passed")

    @staticmethod
    def _pass(definition: ValidatorDefinition, message: str) -> ValidationResult:
        return ValidationResult(
            validator_id=definition.id,
            validator_code=definition.code,
            validator_name=definition.name,
            passed=True,
            severity=definition.severity,
            message=message,
        )

    @staticmethod
    def _fail(
        definition: ValidatorDefinition,
        message: str,
        expected_value: str | None = None,
        actual_value: str | None = None,
    ) -> ValidationResult:
        return ValidationResult(
            validator_id=definition.id,
            validator_code=definition.code,
            validator_name=definition.name,
            passed=False,
            severity=definition.severity,
            message=message,
            expected_value=expected_value,
            actual_value=actual_value,
        )
