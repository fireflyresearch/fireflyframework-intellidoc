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

"""In-memory implementations of catalog ports.

Used by the CLI to run the processing engine without a database.
Catalog data is loaded from YAML files via :mod:`~fireflyframework_intellidoc.catalog.loader`.
"""

from __future__ import annotations

from uuid import UUID

from fireflyframework_intellidoc.catalog.domain.catalog_field import CatalogField
from fireflyframework_intellidoc.catalog.domain.document_type import DocumentType
from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.types import (
    DocumentNature,
    FieldType,
    ValidatorSeverity,
    ValidatorType,
)


class InMemoryDocumentTypeCatalog:
    """Dict-backed document type catalog."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, DocumentType] = {}
        self._by_code: dict[str, DocumentType] = {}

    async def save(self, document_type: DocumentType) -> DocumentType:
        self._by_id[document_type.id] = document_type
        self._by_code[document_type.code] = document_type
        return document_type

    async def find_by_id(self, id: UUID) -> DocumentType | None:
        return self._by_id.get(id)

    async def find_by_code(self, code: str) -> DocumentType | None:
        return self._by_code.get(code)

    async def find_all(
        self,
        *,
        nature: DocumentNature | None = None,
        active_only: bool = True,
        search: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[DocumentType], int]:
        items = list(self._by_id.values())
        if active_only:
            items = [dt for dt in items if dt.is_active]
        if nature:
            items = [dt for dt in items if dt.nature == nature]
        if search:
            q = search.lower()
            items = [dt for dt in items if q in dt.name.lower() or q in dt.code.lower()]
        total = len(items)
        start = page * size
        return items[start : start + size], total

    async def find_all_active(self) -> list[DocumentType]:
        return [dt for dt in self._by_id.values() if dt.is_active]

    async def delete(self, id: UUID) -> None:
        dt = self._by_id.pop(id, None)
        if dt:
            self._by_code.pop(dt.code, None)

    async def count(self, nature: DocumentNature | None = None) -> int:
        items = list(self._by_id.values())
        if nature:
            items = [dt for dt in items if dt.nature == nature]
        return len(items)


class InMemoryFieldCatalog:
    """Dict-backed field catalog."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, CatalogField] = {}
        self._by_code: dict[str, CatalogField] = {}

    async def save(self, field: CatalogField) -> CatalogField:
        self._by_id[field.id] = field
        self._by_code[field.code] = field
        return field

    async def find_by_id(self, id: UUID) -> CatalogField | None:
        return self._by_id.get(id)

    async def find_by_code(self, code: str) -> CatalogField | None:
        return self._by_code.get(code)

    async def find_by_codes(self, codes: list[str]) -> list[CatalogField]:
        return [self._by_code[c] for c in codes if c in self._by_code]

    async def find_all(
        self,
        *,
        field_type: FieldType | None = None,
        active_only: bool = True,
        search: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[CatalogField], int]:
        items = list(self._by_id.values())
        if active_only:
            items = [f for f in items if f.is_active]
        if field_type:
            items = [f for f in items if f.field_type == field_type]
        if search:
            q = search.lower()
            items = [f for f in items if q in f.display_name.lower() or q in f.code.lower()]
        total = len(items)
        start = page * size
        return items[start : start + size], total

    async def delete(self, id: UUID) -> None:
        field = self._by_id.pop(id, None)
        if field:
            self._by_code.pop(field.code, None)


class InMemoryValidatorCatalog:
    """Dict-backed validator catalog."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, ValidatorDefinition] = {}
        self._by_code: dict[str, ValidatorDefinition] = {}

    async def save(self, validator: ValidatorDefinition) -> ValidatorDefinition:
        self._by_id[validator.id] = validator
        self._by_code[validator.code] = validator
        return validator

    async def find_by_id(self, id: UUID) -> ValidatorDefinition | None:
        return self._by_id.get(id)

    async def find_by_code(self, code: str) -> ValidatorDefinition | None:
        return self._by_code.get(code)

    async def find_all(
        self,
        *,
        validator_type: ValidatorType | None = None,
        severity: ValidatorSeverity | None = None,
        nature: DocumentNature | None = None,
        active_only: bool = True,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[ValidatorDefinition], int]:
        items = list(self._by_id.values())
        if active_only:
            items = [v for v in items if v.is_active]
        if validator_type:
            items = [v for v in items if v.validator_type == validator_type]
        if severity:
            items = [v for v in items if v.severity == severity]
        total = len(items)
        start = page * size
        return items[start : start + size], total

    async def find_by_ids(self, ids: list[UUID]) -> list[ValidatorDefinition]:
        return [self._by_id[vid] for vid in ids if vid in self._by_id]

    async def find_for_document_type(
        self, document_type_id: UUID
    ) -> list[ValidatorDefinition]:
        return [
            v
            for v in self._by_id.values()
            if document_type_id in v.applicable_document_types
        ]

    async def delete(self, id: UUID) -> None:
        v = self._by_id.pop(id, None)
        if v:
            self._by_code.pop(v.code, None)
