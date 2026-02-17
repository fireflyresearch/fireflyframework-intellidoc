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

"""Business rule validators — evaluate custom expressions."""

from __future__ import annotations

import logging
import operator
from typing import Any

from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorType

logger = logging.getLogger(__name__)

# Safe operators for expression evaluation
_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


class BusinessRuleValidator:
    """Evaluates custom business rule expressions against extracted data."""

    @property
    def validator_type(self) -> ValidatorType:
        return ValidatorType.BUSINESS_RULE

    async def validate(
        self,
        data: dict[str, Any],
        definition: ValidatorDefinition,
        *,
        pages: list[PageImage] | None = None,
    ) -> ValidationResult:
        expression = definition.rule_expression or definition.config.get(
            "expression", ""
        )
        if not expression:
            return self._pass(definition, "No business rule expression configured")

        try:
            result = self._evaluate(expression, data)
            if result:
                return self._pass(
                    definition, f"Business rule passed: {expression}"
                )
            return self._fail(
                definition,
                f"Business rule failed: {expression}",
            )
        except Exception as exc:
            return self._fail(
                definition,
                f"Error evaluating rule '{expression}': {exc}",
            )

    def _evaluate(self, expression: str, data: dict[str, Any]) -> bool:
        """Evaluate a simple comparison expression.

        Supports: ``field_name operator value`` or
        ``field_a operator field_b`` forms.
        E.g., ``total_amount > 0``, ``start_date <= end_date``
        """
        for op_str, op_func in sorted(
            _OPERATORS.items(), key=lambda x: -len(x[0])
        ):
            if op_str in expression:
                parts = expression.split(op_str, 1)
                if len(parts) == 2:
                    left = self._resolve(parts[0].strip(), data)
                    right = self._resolve(parts[1].strip(), data)
                    return op_func(left, right)

        raise ValueError(f"Unsupported expression format: {expression}")

    @staticmethod
    def _resolve(token: str, data: dict[str, Any]) -> Any:
        """Resolve a token to a value — field reference or literal."""
        if token in data:
            return data[token]
        # Try numeric literal
        try:
            return float(token)
        except ValueError:
            pass
        # Try boolean
        if token.lower() in ("true", "false"):
            return token.lower() == "true"
        # String literal (quoted)
        if (token.startswith('"') and token.endswith('"')) or (
            token.startswith("'") and token.endswith("'")
        ):
            return token[1:-1]
        return token

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
    def _fail(definition: ValidatorDefinition, message: str) -> ValidationResult:
        return ValidationResult(
            validator_id=definition.id,
            validator_code=definition.code,
            validator_name=definition.name,
            passed=False,
            severity=definition.severity,
            message=message,
        )
