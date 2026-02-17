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

"""Validation application service.

Loads validators assigned to a document type from the catalog
and runs them through the :class:`ValidationEngine`.  Also runs
field-level validation rules embedded in :class:`CatalogField`
definitions.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid4

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.catalog.domain.catalog_field import CatalogField
from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.catalog.ports.outbound import (
    DocumentTypeCatalogPort,
    ValidatorCatalogPort,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorSeverity
from fireflyframework_intellidoc.validation.engine import ValidationEngine

logger = logging.getLogger(__name__)


@service
class ValidationService:
    """Orchestrates catalog-driven document validation."""

    def __init__(
        self,
        document_type_port: DocumentTypeCatalogPort,
        validator_port: ValidatorCatalogPort,
        validation_engine: ValidationEngine,
    ) -> None:
        self._doc_types = document_type_port
        self._validators = validator_port
        self._engine = validation_engine

    async def validate(
        self,
        pages: list[PageImage],
        extracted_data: dict[str, Any],
        document_type_id: UUID,
        *,
        resolved_fields: list[CatalogField] | None = None,
    ) -> list[ValidationResult]:
        """Run all validators assigned to the document type.

        Also runs field-level validation rules embedded in the
        resolved :class:`CatalogField` definitions.
        """
        results: list[ValidationResult] = []

        # 1. Document-type validators
        doc_type = await self._doc_types.find_by_id(document_type_id)
        if doc_type is not None and doc_type.validator_ids:
            definitions = await self._validators.find_by_ids(doc_type.validator_ids)

            logger.info(
                "Running %d validators for document type '%s'",
                len(definitions),
                doc_type.code,
            )

            doc_type_results = await self._engine.run_validators(
                extracted_data,
                definitions,
                pages=pages,
            )
            results.extend(doc_type_results)

        # 2. Field-level validation rules
        if resolved_fields:
            field_definitions = self._build_field_validators(resolved_fields)
            if field_definitions:
                logger.info(
                    "Running %d field-level validation rules",
                    len(field_definitions),
                )
                field_results = await self._engine.run_validators(
                    extracted_data,
                    field_definitions,
                    pages=pages,
                )
                results.extend(field_results)

        passed = sum(1 for r in results if r.passed)
        failed = sum(
            1 for r in results
            if not r.passed and r.severity == ValidatorSeverity.ERROR
        )
        warned = sum(
            1 for r in results
            if not r.passed and r.severity == ValidatorSeverity.WARNING
        )

        logger.info(
            "Validation complete: %d passed, %d failed, %d warnings",
            passed,
            failed,
            warned,
        )

        return results

    @staticmethod
    def _build_field_validators(
        fields: list[CatalogField],
    ) -> list[ValidatorDefinition]:
        """Convert field-level validation rules to ValidatorDefinition objects."""
        definitions: list[ValidatorDefinition] = []
        for field in fields:
            for rule in field.validation_rules:
                definitions.append(
                    ValidatorDefinition(
                        id=uuid4(),
                        code=f"{field.code}_{rule.rule_type.value}",
                        name=rule.message or f"{field.display_name} {rule.rule_type.value} check",
                        description=rule.message,
                        validator_type=rule.rule_type,
                        severity=rule.severity,
                        config=rule.config,
                        applicable_fields=[field.code],
                    )
                )
        return definitions

    @staticmethod
    def compute_validation_score(results: list[ValidationResult]) -> float:
        """Compute an overall validation score from 0.0 to 1.0."""
        if not results:
            return 1.0

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        return passed / total

    @staticmethod
    def is_valid(results: list[ValidationResult]) -> bool:
        """Check if all error-severity validations passed."""
        return all(
            r.passed
            for r in results
            if r.severity == ValidatorSeverity.ERROR
        )
