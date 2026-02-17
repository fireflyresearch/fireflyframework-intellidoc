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

"""REST controller for Validator catalog management.

Provides full CRUD operations for validation rule definitions,
including validator type metadata and per-document-type queries.
"""

from __future__ import annotations

from uuid import UUID

from pyfly.container.stereotypes import rest_controller
from pyfly.web.mappings import (
    delete_mapping,
    get_mapping,
    post_mapping,
    put_mapping,
    request_mapping,
)
from pyfly.web.params import Body, PathVar, QueryParam, Valid

from fireflyframework_intellidoc.catalog.exposure.schemas import (
    CreateValidatorRequest,
    PageResponse,
    UpdateValidatorRequest,
    ValidatorResponse,
    ValidatorTypeInfo,
)
from fireflyframework_intellidoc.catalog.service import CatalogService
from fireflyframework_intellidoc.types import (
    DocumentNature,
    ValidatorSeverity,
    ValidatorType,
)


@rest_controller
@request_mapping("/api/v1/intellidoc/validators")
class ValidatorController:
    """CRUD operations for the validator catalog."""

    def __init__(self, catalog_service: CatalogService) -> None:
        self._catalog = catalog_service

    @post_mapping("", status_code=201)
    async def create(
        self, dto: Valid[Body[CreateValidatorRequest]]
    ) -> ValidatorResponse:
        validator = await self._catalog.create_validator(dto)
        return ValidatorResponse.from_domain(validator)

    @get_mapping("")
    async def list_all(
        self,
        validator_type: QueryParam[ValidatorType | None] = None,
        severity: QueryParam[ValidatorSeverity | None] = None,
        nature: QueryParam[DocumentNature | None] = None,
        active_only: QueryParam[bool] = True,
        page: QueryParam[int] = 0,
        size: QueryParam[int] = 20,
    ) -> PageResponse[ValidatorResponse]:
        items, total = await self._catalog.list_validators(
            validator_type=validator_type,
            severity=severity,
            nature=nature,
            active_only=active_only,
            page=page,
            size=size,
        )
        responses = [ValidatorResponse.from_domain(v) for v in items]
        return PageResponse.of(responses, total, page, size)

    @get_mapping("/{validator_id}")
    async def get_by_id(
        self, validator_id: PathVar[UUID]
    ) -> ValidatorResponse:
        validator = await self._catalog.get_validator(validator_id)
        return ValidatorResponse.from_domain(validator)

    @put_mapping("/{validator_id}")
    async def update(
        self,
        validator_id: PathVar[UUID],
        dto: Valid[Body[UpdateValidatorRequest]],
    ) -> ValidatorResponse:
        validator = await self._catalog.update_validator(validator_id, dto)
        return ValidatorResponse.from_domain(validator)

    @delete_mapping("/{validator_id}", status_code=204)
    async def delete(self, validator_id: PathVar[UUID]) -> None:
        await self._catalog.delete_validator(validator_id)

    @get_mapping("/types")
    async def list_types(self) -> list[ValidatorTypeInfo]:
        types = await self._catalog.list_validator_types()
        return [ValidatorTypeInfo(**t) for t in types]

    @get_mapping("/by-document-type/{document_type_id}")
    async def list_for_document_type(
        self, document_type_id: PathVar[UUID]
    ) -> list[ValidatorResponse]:
        validators = await self._catalog.list_validators_for_document_type(
            document_type_id
        )
        return [ValidatorResponse.from_domain(v) for v in validators]
