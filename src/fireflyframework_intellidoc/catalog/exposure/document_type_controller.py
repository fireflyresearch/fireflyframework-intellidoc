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

"""REST controller for Document Type catalog management.

Provides full CRUD operations for document types including
default field assignment and validator management.
"""

from __future__ import annotations

from uuid import UUID

from pyfly.container.stereotypes import rest_controller
from pyfly.web.mappings import (
    delete_mapping,
    get_mapping,
    patch_mapping,
    post_mapping,
    put_mapping,
    request_mapping,
)
from pyfly.web.params import Body, PathVar, QueryParam, Valid

from fireflyframework_intellidoc.catalog.exposure.schemas import (
    AssignValidatorsRequest,
    CreateDocumentTypeRequest,
    DocumentTypeResponse,
    NatureResponse,
    PageResponse,
    SetDefaultFieldsRequest,
    ToggleStatusRequest,
    UpdateDocumentTypeRequest,
)
from fireflyframework_intellidoc.catalog.service import CatalogService
from fireflyframework_intellidoc.types import DocumentNature


@rest_controller
@request_mapping("/api/v1/intellidoc/document-types")
class DocumentTypeController:
    """CRUD operations for the document type catalog."""

    def __init__(self, catalog_service: CatalogService) -> None:
        self._catalog = catalog_service

    @post_mapping("", status_code=201)
    async def create(
        self, dto: Valid[Body[CreateDocumentTypeRequest]]
    ) -> DocumentTypeResponse:
        doc_type = await self._catalog.create_document_type(dto)
        return DocumentTypeResponse.from_domain(doc_type)

    @get_mapping("")
    async def list_all(
        self,
        nature: QueryParam[DocumentNature | None] = None,
        active_only: QueryParam[bool] = True,
        search: QueryParam[str | None] = None,
        page: QueryParam[int] = 0,
        size: QueryParam[int] = 20,
    ) -> PageResponse[DocumentTypeResponse]:
        items, total = await self._catalog.list_document_types(
            nature=nature,
            active_only=active_only,
            search=search,
            page=page,
            size=size,
        )
        responses = [DocumentTypeResponse.from_domain(dt) for dt in items]
        return PageResponse.of(responses, total, page, size)

    @get_mapping("/{document_type_id}")
    async def get_by_id(
        self, document_type_id: PathVar[UUID]
    ) -> DocumentTypeResponse:
        doc_type = await self._catalog.get_document_type(document_type_id)
        return DocumentTypeResponse.from_domain(doc_type)

    @put_mapping("/{document_type_id}")
    async def update(
        self,
        document_type_id: PathVar[UUID],
        dto: Valid[Body[UpdateDocumentTypeRequest]],
    ) -> DocumentTypeResponse:
        doc_type = await self._catalog.update_document_type(document_type_id, dto)
        return DocumentTypeResponse.from_domain(doc_type)

    @delete_mapping("/{document_type_id}", status_code=204)
    async def delete(self, document_type_id: PathVar[UUID]) -> None:
        await self._catalog.delete_document_type(document_type_id)

    @patch_mapping("/{document_type_id}/status")
    async def toggle_status(
        self,
        document_type_id: PathVar[UUID],
        dto: Valid[Body[ToggleStatusRequest]],
    ) -> DocumentTypeResponse:
        doc_type = await self._catalog.toggle_document_type_status(
            document_type_id, dto.is_active
        )
        return DocumentTypeResponse.from_domain(doc_type)

    @put_mapping("/{document_type_id}/default-fields")
    async def set_default_fields(
        self,
        document_type_id: PathVar[UUID],
        dto: Valid[Body[SetDefaultFieldsRequest]],
    ) -> DocumentTypeResponse:
        doc_type = await self._catalog.set_default_field_codes(
            document_type_id, dto.field_codes
        )
        return DocumentTypeResponse.from_domain(doc_type)

    @get_mapping("/natures")
    async def list_natures(self) -> list[NatureResponse]:
        natures = await self._catalog.list_natures()
        return [NatureResponse(**n) for n in natures]

    @post_mapping("/{document_type_id}/validators")
    async def assign_validators(
        self,
        document_type_id: PathVar[UUID],
        dto: Valid[Body[AssignValidatorsRequest]],
    ) -> DocumentTypeResponse:
        doc_type = await self._catalog.assign_validators(
            document_type_id, dto.validator_ids
        )
        return DocumentTypeResponse.from_domain(doc_type)
