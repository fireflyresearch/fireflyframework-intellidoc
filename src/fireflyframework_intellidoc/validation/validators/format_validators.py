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

"""Format validators — regex, date, email, phone, currency, IBAN."""

from __future__ import annotations

import re
from typing import Any

from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorType

# Common format patterns
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
PHONE_PATTERN = re.compile(
    r"^\+?[\d\s\-().]{7,20}$"
)
IBAN_PATTERN = re.compile(
    r"^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$"
)


class FormatValidator:
    """Validates field values against format rules."""

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.FORMAT

    async def validate(
        self,
        data: dict[str, Any],
        definition: ValidatorDefinition,
        *,
        pages: list[PageImage] | None = None,
    ) -> ValidationResult:
        field_name = (
            definition.applicable_fields[0]
            if definition.applicable_fields
            else None
        )
        if field_name is None:
            return self._pass(definition)

        value = data.get(field_name)
        if value is None:
            return self._pass(definition, message="Field not present, skipping format check")

        value_str = str(value)
        fmt = definition.config.get("format", "")
        pattern = definition.config.get("pattern", "")

        if fmt == "email":
            return self._check_regex(definition, value_str, EMAIL_PATTERN, field_name, "email")
        if fmt == "phone":
            return self._check_regex(definition, value_str, PHONE_PATTERN, field_name, "phone")
        if fmt == "iban":
            return self._check_iban(definition, value_str, field_name)
        if pattern:
            try:
                compiled = re.compile(pattern)
            except re.error:
                return self._fail(
                    definition, f"Invalid regex pattern: {pattern}", field_name
                )
            return self._check_regex(definition, value_str, compiled, field_name, "pattern")

        return self._pass(definition, message="No format rule configured")

    def _check_regex(
        self,
        definition: ValidatorDefinition,
        value: str,
        pattern: re.Pattern[str],
        field_name: str,
        format_name: str,
    ) -> ValidationResult:
        if pattern.match(value):
            return self._pass(definition, field_name=field_name)
        return self._fail(
            definition,
            f"Value '{value}' does not match {format_name} format",
            field_name,
            expected_value=f"Pattern: {pattern.pattern}",
            actual_value=value,
        )

    def _check_iban(
        self,
        definition: ValidatorDefinition,
        value: str,
        field_name: str,
    ) -> ValidationResult:
        cleaned = value.replace(" ", "").upper()
        if not IBAN_PATTERN.match(cleaned):
            return self._fail(
                definition, f"Invalid IBAN format: {value}", field_name
            )
        # MOD 97 check
        rearranged = cleaned[4:] + cleaned[:4]
        numeric = ""
        for ch in rearranged:
            if ch.isdigit():
                numeric += ch
            else:
                numeric += str(ord(ch) - 55)
        if int(numeric) % 97 != 1:
            return self._fail(
                definition, f"IBAN checksum failed: {value}", field_name
            )
        return self._pass(definition, field_name=field_name)

    @staticmethod
    def _pass(
        definition: ValidatorDefinition,
        message: str = "",
        field_name: str | None = None,
    ) -> ValidationResult:
        return ValidationResult(
            validator_id=definition.id,
            validator_code=definition.code,
            validator_name=definition.name,
            passed=True,
            severity=definition.severity,
            message=message,
            field_name=field_name,
        )

    @staticmethod
    def _fail(
        definition: ValidatorDefinition,
        message: str,
        field_name: str | None = None,
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
            field_name=field_name,
            expected_value=expected_value,
            actual_value=actual_value,
        )
