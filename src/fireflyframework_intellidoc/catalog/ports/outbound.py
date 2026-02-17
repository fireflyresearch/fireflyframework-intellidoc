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

"""Outbound ports for the catalog domain.

These Protocol interfaces decouple catalog business logic from the
underlying persistence mechanism (relational DB, document DB, etc.).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
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


@runtime_checkable
class DocumentTypeCatalogPort(Protocol):
    """Port for persisting document type catalog entries."""

    async def save(self, document_type: DocumentType) -> DocumentType: ...

    async def find_by_id(self, id: UUID) -> DocumentType | None: ...

    async def find_by_code(self, code: str) -> DocumentType | None: ...

    async def find_all(
        self,
        *,
        nature: DocumentNature | None = None,
        active_only: bool = True,
        search: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[DocumentType], int]: ...

    async def find_all_active(self) -> list[DocumentType]: ...

    async def delete(self, id: UUID) -> None: ...

    async def count(self, nature: DocumentNature | None = None) -> int: ...


@runtime_checkable
class ValidatorCatalogPort(Protocol):
    """Port for persisting validator catalog entries."""

    async def save(self, validator: ValidatorDefinition) -> ValidatorDefinition: ...

    async def find_by_id(self, id: UUID) -> ValidatorDefinition | None: ...

    async def find_by_code(self, code: str) -> ValidatorDefinition | None: ...

    async def find_all(
        self,
        *,
        validator_type: ValidatorType | None = None,
        severity: ValidatorSeverity | None = None,
        nature: DocumentNature | None = None,
        active_only: bool = True,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[ValidatorDefinition], int]: ...

    async def find_by_ids(self, ids: list[UUID]) -> list[ValidatorDefinition]: ...

    async def find_for_document_type(
        self, document_type_id: UUID
    ) -> list[ValidatorDefinition]: ...

    async def delete(self, id: UUID) -> None: ...


@runtime_checkable
class FieldCatalogPort(Protocol):
    """Port for persisting catalog field definitions."""

    async def save(self, field: CatalogField) -> CatalogField: ...

    async def find_by_id(self, id: UUID) -> CatalogField | None: ...

    async def find_by_code(self, code: str) -> CatalogField | None: ...

    async def find_by_codes(self, codes: list[str]) -> list[CatalogField]: ...

    async def find_all(
        self,
        *,
        field_type: FieldType | None = None,
        active_only: bool = True,
        search: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[CatalogField], int]: ...

    async def delete(self, id: UUID) -> None: ...
