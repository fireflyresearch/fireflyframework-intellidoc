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

"""Catalog loader — YAML to domain objects.

Parses a ``catalog.yaml`` file and populates in-memory catalog adapters
with :class:`DocumentType`, :class:`CatalogField`, and
:class:`ValidatorDefinition` domain objects.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from fireflyframework_intellidoc.catalog.adapters.memory import (
    InMemoryDocumentTypeCatalog,
    InMemoryFieldCatalog,
    InMemoryValidatorCatalog,
)
from fireflyframework_intellidoc.catalog.domain.catalog_field import (
    CatalogField,
    FieldValidationRule,
)
from fireflyframework_intellidoc.catalog.domain.document_type import DocumentType
from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)

logger = logging.getLogger(__name__)


class CatalogLoader:
    """Loads catalog definitions from a YAML file into in-memory adapters."""

    def __init__(
        self,
        doc_type_catalog: InMemoryDocumentTypeCatalog,
        field_catalog: InMemoryFieldCatalog,
        validator_catalog: InMemoryValidatorCatalog,
    ) -> None:
        self._doc_types = doc_type_catalog
        self._fields = field_catalog
        self._validators = validator_catalog

    async def load(self, path: Path) -> dict[str, int]:
        """Load catalog from YAML and return counts of loaded entities."""
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            raise ValueError(f"Invalid catalog file: {path}")

        counts: dict[str, int] = {"document_types": 0, "fields": 0, "validators": 0}

        # Load fields first (document types reference them by code)
        for field_data in data.get("fields", []):
            field = self._parse_field(field_data)
            await self._fields.save(field)
            counts["fields"] += 1

        # Load validators
        for validator_data in data.get("validators", []):
            validator = ValidatorDefinition(**validator_data)
            await self._validators.save(validator)
            counts["validators"] += 1

        # Load document types
        for dt_data in data.get("document_types", []):
            doc_type = DocumentType(**dt_data)
            await self._doc_types.save(doc_type)
            counts["document_types"] += 1

        logger.info(
            "Loaded catalog: %d types, %d fields, %d validators",
            counts["document_types"],
            counts["fields"],
            counts["validators"],
        )
        return counts

    def _parse_field(self, data: dict[str, Any]) -> CatalogField:
        """Parse a field dict, handling nested validation_rules and table_columns."""
        rules_data = data.pop("validation_rules", [])
        columns_data = data.pop("table_columns", None)

        rules = [FieldValidationRule(**r) for r in rules_data]

        columns = None
        if columns_data:
            columns = [self._parse_field(c) for c in columns_data]

        return CatalogField(**data, validation_rules=rules, table_columns=columns)
