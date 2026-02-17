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

"""Validation engine.

:class:`ValidationEngine` loads validator definitions from the catalog
and dispatches each to the appropriate :class:`ValidatorPort` handler
based on its :attr:`validator_type`.
"""

from __future__ import annotations

import logging
from typing import Any

from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorType
from fireflyframework_intellidoc.validation.ports.outbound import ValidatorPort

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Dispatches validator definitions to the appropriate handler.

    Maintains a registry of :class:`ValidatorPort` implementations
    keyed by :class:`ValidatorType`.
    """

    def __init__(self, validators: list[ValidatorPort]) -> None:
        self._handlers: dict[ValidatorType, ValidatorPort] = {}
        for v in validators:
            self._handlers[v.validator_type] = v

    async def run_validators(
        self,
        data: dict[str, Any],
        definitions: list[ValidatorDefinition],
        *,
        pages: list[PageImage] | None = None,
    ) -> list[ValidationResult]:
        """Execute all validator definitions against the extracted data."""
        results: list[ValidationResult] = []

        for definition in definitions:
            if not definition.is_active:
                continue

            handler = self._handlers.get(definition.validator_type)
            if handler is None:
                logger.warning(
                    "No handler registered for validator type '%s' "
                    "(validator: %s)",
                    definition.validator_type,
                    definition.code,
                )
                results.append(
                    ValidationResult(
                        validator_id=definition.id,
                        validator_code=definition.code,
                        validator_name=definition.name,
                        passed=False,
                        severity=definition.severity,
                        message=f"No handler for validator type: {definition.validator_type}",
                    )
                )
                continue

            try:
                result = await handler.validate(
                    data, definition, pages=pages
                )
                results.append(result)

                log_level = (
                    logging.DEBUG if result.passed else logging.WARNING
                )
                logger.log(
                    log_level,
                    "Validator '%s' %s: %s",
                    definition.code,
                    "passed" if result.passed else "FAILED",
                    result.message,
                )
            except Exception as exc:
                logger.error(
                    "Validator '%s' raised exception: %s",
                    definition.code,
                    exc,
                )
                results.append(
                    ValidationResult(
                        validator_id=definition.id,
                        validator_code=definition.code,
                        validator_name=definition.name,
                        passed=False,
                        severity=definition.severity,
                        message=f"Validator error: {exc}",
                    )
                )

        return results

    @property
    def registered_types(self) -> list[ValidatorType]:
        return list(self._handlers.keys())
