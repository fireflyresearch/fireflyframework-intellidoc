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

"""REST controller for Fields Catalog management.

Provides full CRUD operations for reusable field definitions
in the fields catalog.
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
    CatalogFieldResponse,
    CreateFieldRequest,
    PageResponse,
    UpdateFieldRequest,
)
from fireflyframework_intellidoc.catalog.service import CatalogService
from fireflyframework_intellidoc.types import FieldType


@rest_controller
@request_mapping("/api/v1/intellidoc/fields")
class FieldController:
    """CRUD operations for the fields catalog."""

    def __init__(self, catalog_service: CatalogService) -> None:
        self._catalog = catalog_service

    @post_mapping("", status_code=201)
    async def create_field(
        self, dto: Valid[Body[CreateFieldRequest]]
    ) -> CatalogFieldResponse:
        field = await self._catalog.create_field(dto)
        return CatalogFieldResponse.from_domain(field)

    @get_mapping("")
    async def list_fields(
        self,
        field_type: QueryParam[FieldType | None] = None,
        active_only: QueryParam[bool] = True,
        search: QueryParam[str | None] = None,
        page: QueryParam[int] = 0,
        size: QueryParam[int] = 20,
    ) -> PageResponse[CatalogFieldResponse]:
        items, total = await self._catalog.list_fields(
            field_type=field_type,
            active_only=active_only,
            search=search,
            page=page,
            size=size,
        )
        responses = [CatalogFieldResponse.from_domain(f) for f in items]
        return PageResponse.of(responses, total, page, size)

    @get_mapping("/{field_id}")
    async def get_by_id(
        self, field_id: PathVar[UUID]
    ) -> CatalogFieldResponse:
        field = await self._catalog.get_field(field_id)
        return CatalogFieldResponse.from_domain(field)

    @get_mapping("/by-code/{code}")
    async def get_by_code(
        self, code: PathVar[str]
    ) -> CatalogFieldResponse:
        field = await self._catalog.get_field_by_code(code)
        return CatalogFieldResponse.from_domain(field)

    @put_mapping("/{field_id}")
    async def update_field(
        self,
        field_id: PathVar[UUID],
        dto: Valid[Body[UpdateFieldRequest]],
    ) -> CatalogFieldResponse:
        field = await self._catalog.update_field(field_id, dto)
        return CatalogFieldResponse.from_domain(field)

    @delete_mapping("/{field_id}", status_code=204)
    async def delete_field(self, field_id: PathVar[UUID]) -> None:
        await self._catalog.delete_field(field_id)
