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

"""Catalog application service.

:class:`CatalogService` encapsulates the business logic for managing
document types, validators, and the fields catalog.  It depends only
on port interfaces, keeping the service independent of persistence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.catalog.domain.catalog_field import (
    CatalogField,
    FieldValidationRule,
)
from fireflyframework_intellidoc.catalog.domain.document_type import DocumentType
from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.catalog.exposure.schemas import (
    CreateDocumentTypeRequest,
    CreateFieldRequest,
    CreateValidatorRequest,
    UpdateDocumentTypeRequest,
    UpdateFieldRequest,
    UpdateValidatorRequest,
)
from fireflyframework_intellidoc.catalog.ports.outbound import (
    DocumentTypeCatalogPort,
    FieldCatalogPort,
    ValidatorCatalogPort,
)
from fireflyframework_intellidoc.exceptions import (
    DocumentTypeAlreadyExistsException,
    DocumentTypeNotFoundException,
    FieldAlreadyExistsException,
    FieldNotFoundException,
    TargetSchemaResolutionException,
    ValidatorAlreadyExistsException,
    ValidatorNotFoundException,
)
from fireflyframework_intellidoc.types import (
    DocumentNature,
    FieldType,
    ValidatorSeverity,
    ValidatorType,
)


@service
class CatalogService:
    """Application service for the document type and validator catalog."""

    def __init__(
        self,
        document_type_port: DocumentTypeCatalogPort,
        validator_port: ValidatorCatalogPort,
        field_port: FieldCatalogPort,
    ) -> None:
        self._doc_types = document_type_port
        self._validators = validator_port
        self._fields = field_port

    # ── Document Types ────────────────────────────────────────────────

    async def create_document_type(
        self, request: CreateDocumentTypeRequest
    ) -> DocumentType:
        existing = await self._doc_types.find_by_code(request.code)
        if existing is not None:
            raise DocumentTypeAlreadyExistsException(request.code)

        doc_type = DocumentType(
            code=request.code,
            name=request.name,
            description=request.description,
            nature=request.nature,
            visual_description=request.visual_description,
            visual_cues=request.visual_cues,
            sample_keywords=request.sample_keywords,
            classification_instructions=request.classification_instructions,
            classification_confidence_threshold=request.classification_confidence_threshold,
            extraction_instructions=request.extraction_instructions,
            default_field_codes=request.default_field_codes,
            tags=request.tags,
            supported_languages=request.supported_languages,
        )
        return await self._doc_types.save(doc_type)

    async def get_document_type(self, document_type_id: UUID) -> DocumentType:
        doc_type = await self._doc_types.find_by_id(document_type_id)
        if doc_type is None:
            raise DocumentTypeNotFoundException(str(document_type_id))
        return doc_type

    async def get_document_type_by_code(self, code: str) -> DocumentType:
        doc_type = await self._doc_types.find_by_code(code)
        if doc_type is None:
            raise DocumentTypeNotFoundException(code)
        return doc_type

    async def list_document_types(
        self,
        *,
        nature: DocumentNature | None = None,
        active_only: bool = True,
        search: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[DocumentType], int]:
        return await self._doc_types.find_all(
            nature=nature,
            active_only=active_only,
            search=search,
            page=page,
            size=size,
        )

    async def update_document_type(
        self,
        document_type_id: UUID,
        request: UpdateDocumentTypeRequest,
    ) -> DocumentType:
        doc_type = await self.get_document_type(document_type_id)

        updates = request.model_dump(exclude_none=True)
        for field_name, value in updates.items():
            setattr(doc_type, field_name, value)
        doc_type.updated_at = datetime.now()

        return await self._doc_types.save(doc_type)

    async def delete_document_type(self, document_type_id: UUID) -> None:
        await self.get_document_type(document_type_id)
        await self._doc_types.delete(document_type_id)

    async def toggle_document_type_status(
        self, document_type_id: UUID, is_active: bool
    ) -> DocumentType:
        doc_type = await self.get_document_type(document_type_id)
        doc_type.is_active = is_active
        doc_type.updated_at = datetime.now()
        return await self._doc_types.save(doc_type)

    async def set_default_field_codes(
        self, document_type_id: UUID, field_codes: list[str]
    ) -> DocumentType:
        await self.resolve_fields(field_codes)
        doc_type = await self.get_document_type(document_type_id)
        doc_type.default_field_codes = field_codes
        doc_type.updated_at = datetime.now()
        return await self._doc_types.save(doc_type)

    async def assign_validators(
        self, document_type_id: UUID, validator_ids: list[UUID]
    ) -> DocumentType:
        doc_type = await self.get_document_type(document_type_id)
        for vid in validator_ids:
            v = await self._validators.find_by_id(vid)
            if v is None:
                raise ValidatorNotFoundException(str(vid))
        doc_type.validator_ids = validator_ids
        doc_type.updated_at = datetime.now()
        return await self._doc_types.save(doc_type)

    async def list_natures(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for nature in DocumentNature:
            count = await self._doc_types.count(nature=nature)
            result.append(
                {
                    "code": nature.value,
                    "name": nature.name.replace("_", " ").title(),
                    "document_type_count": count,
                }
            )
        return result

    async def list_all_active_document_types(self) -> list[DocumentType]:
        return await self._doc_types.find_all_active()

    # ── Fields Catalog ───────────────────────────────────────────────

    async def create_field(self, request: CreateFieldRequest) -> CatalogField:
        existing = await self._fields.find_by_code(request.code)
        if existing is not None:
            raise FieldAlreadyExistsException(request.code)

        field = self._to_catalog_field(request)
        return await self._fields.save(field)

    async def get_field(self, field_id: UUID) -> CatalogField:
        field = await self._fields.find_by_id(field_id)
        if field is None:
            raise FieldNotFoundException(str(field_id))
        return field

    async def get_field_by_code(self, code: str) -> CatalogField:
        field = await self._fields.find_by_code(code)
        if field is None:
            raise FieldNotFoundException(code)
        return field

    async def list_fields(
        self,
        *,
        field_type: FieldType | None = None,
        active_only: bool = True,
        search: str | None = None,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[CatalogField], int]:
        return await self._fields.find_all(
            field_type=field_type,
            active_only=active_only,
            search=search,
            page=page,
            size=size,
        )

    async def update_field(
        self,
        field_id: UUID,
        request: UpdateFieldRequest,
    ) -> CatalogField:
        field = await self.get_field(field_id)

        updates = request.model_dump(exclude_none=True)

        # Handle nested table_columns conversion
        if "table_columns" in updates and updates["table_columns"] is not None:
            updates["table_columns"] = [
                self._to_catalog_field(CreateFieldRequest(**c))
                for c in updates["table_columns"]
            ]

        # Handle nested validation_rules conversion
        if "validation_rules" in updates and updates["validation_rules"] is not None:
            updates["validation_rules"] = [
                FieldValidationRule(**r) for r in updates["validation_rules"]
            ]

        for field_name, value in updates.items():
            setattr(field, field_name, value)
        field.updated_at = datetime.now()

        return await self._fields.save(field)

    async def delete_field(self, field_id: UUID) -> None:
        await self.get_field(field_id)
        await self._fields.delete(field_id)

    async def resolve_fields(self, field_codes: list[str]) -> list[CatalogField]:
        """Resolve field codes to domain objects.

        Raises :class:`TargetSchemaResolutionException` if any codes
        are missing from the catalog.
        """
        resolved = await self._fields.find_by_codes(field_codes)
        resolved_codes = {f.code for f in resolved}
        missing = [c for c in field_codes if c not in resolved_codes]
        if missing:
            raise TargetSchemaResolutionException(missing)
        return resolved

    async def get_default_fields(
        self, document_type_id: UUID
    ) -> list[CatalogField]:
        """Load a document type's default fields from the catalog."""
        doc_type = await self.get_document_type(document_type_id)
        if not doc_type.default_field_codes:
            return []
        return await self.resolve_fields(doc_type.default_field_codes)

    # ── Validators ────────────────────────────────────────────────────

    async def create_validator(
        self, request: CreateValidatorRequest
    ) -> ValidatorDefinition:
        existing = await self._validators.find_by_code(request.code)
        if existing is not None:
            raise ValidatorAlreadyExistsException(request.code)

        validator = ValidatorDefinition(
            code=request.code,
            name=request.name,
            description=request.description,
            validator_type=request.validator_type,
            severity=request.severity,
            config=request.config,
            applicable_natures=request.applicable_natures,
            applicable_document_types=request.applicable_document_types,
            applicable_fields=request.applicable_fields,
            visual_prompt=request.visual_prompt,
            visual_expected=request.visual_expected,
            rule_expression=request.rule_expression,
        )
        return await self._validators.save(validator)

    async def get_validator(self, validator_id: UUID) -> ValidatorDefinition:
        validator = await self._validators.find_by_id(validator_id)
        if validator is None:
            raise ValidatorNotFoundException(str(validator_id))
        return validator

    async def list_validators(
        self,
        *,
        validator_type: ValidatorType | None = None,
        severity: ValidatorSeverity | None = None,
        nature: DocumentNature | None = None,
        active_only: bool = True,
        page: int = 0,
        size: int = 20,
    ) -> tuple[list[ValidatorDefinition], int]:
        return await self._validators.find_all(
            validator_type=validator_type,
            severity=severity,
            nature=nature,
            active_only=active_only,
            page=page,
            size=size,
        )

    async def update_validator(
        self,
        validator_id: UUID,
        request: UpdateValidatorRequest,
    ) -> ValidatorDefinition:
        validator = await self.get_validator(validator_id)

        updates = request.model_dump(exclude_none=True)
        for field_name, value in updates.items():
            setattr(validator, field_name, value)
        validator.updated_at = datetime.now()

        return await self._validators.save(validator)

    async def delete_validator(self, validator_id: UUID) -> None:
        await self.get_validator(validator_id)
        await self._validators.delete(validator_id)

    async def list_validators_for_document_type(
        self, document_type_id: UUID
    ) -> list[ValidatorDefinition]:
        await self.get_document_type(document_type_id)
        return await self._validators.find_for_document_type(document_type_id)

    async def list_validator_types(self) -> list[dict[str, Any]]:
        return [
            {
                "code": vt.value,
                "name": vt.name.replace("_", " ").title(),
                "description": _VALIDATOR_TYPE_DESCRIPTIONS.get(vt, ""),
                "config_schema": _VALIDATOR_TYPE_SCHEMAS.get(vt, {}),
            }
            for vt in ValidatorType
        ]

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _to_catalog_field(req: CreateFieldRequest) -> CatalogField:
        table_columns = None
        if req.table_columns:
            table_columns = [
                CatalogService._to_catalog_field(c) for c in req.table_columns
            ]
        return CatalogField(
            code=req.code,
            display_name=req.display_name,
            field_type=req.field_type,
            description=req.description,
            required=req.required,
            default_value=req.default_value,
            format_pattern=req.format_pattern,
            min_value=req.min_value,
            max_value=req.max_value,
            allowed_values=req.allowed_values,
            table_columns=table_columns,
            location_hint=req.location_hint,
            validation_rules=[
                FieldValidationRule(
                    rule_type=r.rule_type,
                    severity=r.severity,
                    config=r.config,
                    message=r.message,
                )
                for r in req.validation_rules
            ],
            tags=req.tags,
        )


# ── Validator type metadata ──────────────────────────────────────────

_VALIDATOR_TYPE_DESCRIPTIONS: dict[ValidatorType, str] = {
    ValidatorType.FORMAT: "Validates field values against format rules (regex, date, email, etc.)",
    ValidatorType.RANGE: "Validates numeric or date values fall within a specified range",
    ValidatorType.REQUIRED: "Ensures required fields are present and non-empty",
    ValidatorType.CROSS_FIELD: "Validates consistency between multiple fields",
    ValidatorType.VISUAL: "Uses VLM to perform visual checks (signatures, stamps, photos)",
    ValidatorType.BUSINESS_RULE: "Evaluates custom business rule expressions",
    ValidatorType.COMPLETENESS: "Checks document completeness (pages, field coverage)",
    ValidatorType.CHECKSUM: "Validates check digits and checksums (Luhn, MOD 97)",
    ValidatorType.LOOKUP: "Validates values against external data sources",
}

_VALIDATOR_TYPE_SCHEMAS: dict[ValidatorType, dict[str, Any]] = {
    ValidatorType.FORMAT: {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern"},
            "format": {"type": "string", "enum": ["date", "email", "phone", "currency", "iban"]},
        },
    },
    ValidatorType.RANGE: {
        "type": "object",
        "properties": {
            "min": {"type": "number"},
            "max": {"type": "number"},
            "after": {"type": "string", "description": "ISO date"},
            "before": {"type": "string", "description": "ISO date"},
        },
    },
    ValidatorType.REQUIRED: {
        "type": "object",
        "properties": {
            "condition": {"type": "string", "description": "Conditional expression"},
        },
    },
    ValidatorType.CROSS_FIELD: {
        "type": "object",
        "properties": {
            "fields": {"type": "array", "items": {"type": "string"}},
            "total_field": {"type": "string"},
            "rule": {"type": "string", "enum": ["match", "sum", "date_order"]},
        },
    },
    ValidatorType.VISUAL: {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "expected": {"type": "string"},
        },
    },
    ValidatorType.BUSINESS_RULE: {
        "type": "object",
        "properties": {
            "expression": {"type": "string"},
        },
    },
    ValidatorType.COMPLETENESS: {
        "type": "object",
        "properties": {
            "min_pages": {"type": "integer"},
            "min_fields_percent": {"type": "number"},
        },
    },
    ValidatorType.CHECKSUM: {
        "type": "object",
        "properties": {
            "algorithm": {"type": "string", "enum": ["luhn", "mod97"]},
        },
    },
    ValidatorType.LOOKUP: {
        "type": "object",
        "properties": {
            "source": {"type": "string"},
            "field": {"type": "string"},
        },
    },
}
