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

"""Cross-field validators — consistency checks between multiple fields."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorType


class CrossFieldValidator:
    """Validates consistency between multiple extracted fields."""

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.CROSS_FIELD

    async def validate(
        self,
        data: dict[str, Any],
        definition: ValidatorDefinition,
        *,
        pages: list[PageImage] | None = None,
    ) -> ValidationResult:
        rule = definition.config.get("rule", "")
        fields = definition.config.get("fields", [])

        if rule == "match":
            return self._check_match(data, fields, definition)
        if rule == "sum":
            total_field = definition.config.get("total_field", "")
            return self._check_sum(data, fields, total_field, definition)
        if rule == "date_order":
            return self._check_date_order(data, fields, definition)

        return ValidationResult(
            validator_id=definition.id,
            validator_code=definition.code,
            validator_name=definition.name,
            passed=True,
            severity=definition.severity,
            message=f"Unknown cross-field rule: {rule}",
        )

    def _check_match(
        self,
        data: dict[str, Any],
        fields: list[str],
        definition: ValidatorDefinition,
    ) -> ValidationResult:
        if len(fields) < 2:
            return self._pass(definition, "Match requires at least 2 fields")

        values = [data.get(f) for f in fields]
        present = [v for v in values if v is not None]

        if len(present) < 2:
            return self._pass(definition, "Not enough fields present to compare")

        if len(set(str(v) for v in present)) == 1:
            return self._pass(definition, f"Fields {fields} match")

        return self._fail(
            definition,
            f"Fields {fields} do not match: {dict(zip(fields, values))}",
        )

    def _check_sum(
        self,
        data: dict[str, Any],
        fields: list[str],
        total_field: str,
        definition: ValidatorDefinition,
    ) -> ValidationResult:
        try:
            total = float(data.get(total_field, 0))
            parts_sum = sum(float(data.get(f, 0)) for f in fields)
            tolerance = definition.config.get("tolerance", 0.01)

            if abs(parts_sum - total) <= tolerance:
                return self._pass(
                    definition,
                    f"Sum of {fields} ({parts_sum}) matches {total_field} ({total})",
                )
            return self._fail(
                definition,
                f"Sum of {fields} ({parts_sum}) does not match "
                f"{total_field} ({total})",
                expected_value=str(total),
                actual_value=str(parts_sum),
            )
        except (ValueError, TypeError) as exc:
            return self._fail(definition, f"Cannot compute sum: {exc}")

    def _check_date_order(
        self,
        data: dict[str, Any],
        fields: list[str],
        definition: ValidatorDefinition,
    ) -> ValidationResult:
        if len(fields) < 2:
            return self._pass(definition, "Date order requires at least 2 fields")

        dates: list[tuple[str, datetime]] = []
        for f in fields:
            val = data.get(f)
            if val is None:
                continue
            try:
                if isinstance(val, datetime):
                    dates.append((f, val))
                else:
                    dates.append((f, datetime.fromisoformat(str(val))))
            except (ValueError, TypeError):
                return self._fail(
                    definition, f"Cannot parse date for field '{f}': {val}"
                )

        if len(dates) < 2:
            return self._pass(definition, "Not enough dates to compare")

        for i in range(len(dates) - 1):
            name_a, date_a = dates[i]
            name_b, date_b = dates[i + 1]
            if date_a > date_b:
                return self._fail(
                    definition,
                    f"Date order violation: {name_a} ({date_a}) is after {name_b} ({date_b})",
                )

        return self._pass(definition, f"Dates in correct order: {fields}")

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
