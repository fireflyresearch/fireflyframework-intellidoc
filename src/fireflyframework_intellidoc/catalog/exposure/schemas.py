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

"""Request/Response DTOs for the Catalog Management APIs.

These Pydantic models define the API contract for document-type,
validator, and extraction-schema endpoints.  They are intentionally
separate from the domain models so input validation rules and
response shaping stay at the boundary layer.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.catalog.domain.catalog_field import (
    CatalogField,
)
from fireflyframework_intellidoc.types import (
    DocumentNature,
    FieldType,
    ValidatorSeverity,
    ValidatorType,
)

T = TypeVar("T")


# ── Pagination ────────────────────────────────────────────────────────


class PageResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    content: list[T]
    page: int
    size: int
    total_elements: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def of(
        cls, items: list[T], total: int, page: int, size: int
    ) -> PageResponse[T]:
        total_pages = max(1, math.ceil(total / size)) if size > 0 else 1
        return cls(
            content=items,
            page=page,
            size=size,
            total_elements=total,
            total_pages=total_pages,
            has_next=page < total_pages - 1,
            has_previous=page > 0,
        )


# ── Document Type DTOs ────────────────────────────────────────────────


class CreateDocumentTypeRequest(BaseModel):
    """Create a new document type in the catalog."""

    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    nature: DocumentNature

    visual_description: str = Field(default="", max_length=2000)
    visual_cues: list[str] = Field(default_factory=list)
    sample_keywords: list[str] = Field(default_factory=list)

    classification_instructions: str = ""
    classification_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    extraction_instructions: str = ""
    default_field_codes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    supported_languages: list[str] = Field(default_factory=lambda: ["en"])


class UpdateDocumentTypeRequest(BaseModel):
    """Partial update for an existing document type."""

    name: str | None = None
    description: str | None = None
    nature: DocumentNature | None = None
    visual_description: str | None = None
    visual_cues: list[str] | None = None
    sample_keywords: list[str] | None = None
    classification_instructions: str | None = None
    classification_confidence_threshold: float | None = Field(
        default=None, ge=0.0, le=1.0
    )
    extraction_instructions: str | None = None
    default_field_codes: list[str] | None = None
    tags: list[str] | None = None
    supported_languages: list[str] | None = None


class ToggleStatusRequest(BaseModel):
    """Toggle the active status of a document type."""

    is_active: bool


class AssignValidatorsRequest(BaseModel):
    """Assign validators to a document type."""

    validator_ids: list[UUID]


class DocumentTypeResponse(BaseModel):
    """Response representation of a document type."""

    id: UUID
    code: str
    name: str
    description: str
    nature: DocumentNature
    visual_description: str
    visual_cues: list[str]
    sample_keywords: list[str]
    classification_instructions: str
    classification_confidence_threshold: float
    extraction_instructions: str
    default_field_codes: list[str]
    default_field_count: int
    validator_ids: list[UUID]
    validator_count: int
    version: str
    is_active: bool
    tags: list[str]
    supported_languages: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, doc_type: Any) -> DocumentTypeResponse:
        return cls(
            id=doc_type.id,
            code=doc_type.code,
            name=doc_type.name,
            description=doc_type.description,
            nature=doc_type.nature,
            visual_description=doc_type.visual_description,
            visual_cues=doc_type.visual_cues,
            sample_keywords=doc_type.sample_keywords,
            classification_instructions=doc_type.classification_instructions,
            classification_confidence_threshold=doc_type.classification_confidence_threshold,
            extraction_instructions=doc_type.extraction_instructions,
            default_field_codes=doc_type.default_field_codes,
            default_field_count=len(doc_type.default_field_codes),
            validator_ids=doc_type.validator_ids,
            validator_count=len(doc_type.validator_ids),
            version=doc_type.version,
            is_active=doc_type.is_active,
            tags=doc_type.tags,
            supported_languages=doc_type.supported_languages,
            created_at=doc_type.created_at,
            updated_at=doc_type.updated_at,
        )


class NatureResponse(BaseModel):
    """Summary of a document nature with its document type count."""

    code: str
    name: str
    document_type_count: int


# ── Field Catalog DTOs ────────────────────────────────────────────────


class FieldValidationRuleRequest(BaseModel):
    """Request DTO for an embedded field validation rule."""

    rule_type: ValidatorType
    severity: ValidatorSeverity = ValidatorSeverity.ERROR
    config: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class CreateFieldRequest(BaseModel):
    """Create a new field in the catalog."""

    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(min_length=1, max_length=200)
    field_type: FieldType
    description: str = ""
    required: bool = False
    default_value: Any = None
    format_pattern: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[str] | None = None
    table_columns: list[CreateFieldRequest] | None = None
    location_hint: str = ""
    validation_rules: list[FieldValidationRuleRequest] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class UpdateFieldRequest(BaseModel):
    """Partial update for an existing catalog field."""

    display_name: str | None = None
    description: str | None = None
    required: bool | None = None
    default_value: Any | None = None
    format_pattern: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[str] | None = None
    table_columns: list[CreateFieldRequest] | None = None
    location_hint: str | None = None
    validation_rules: list[FieldValidationRuleRequest] | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class SetDefaultFieldsRequest(BaseModel):
    """Set default field codes for a document type."""

    field_codes: list[str]


class FieldValidationRuleResponse(BaseModel):
    """Response representation of a field validation rule."""

    rule_type: ValidatorType
    severity: ValidatorSeverity
    config: dict[str, Any]
    message: str


class CatalogFieldResponse(BaseModel):
    """Response representation of a catalog field."""

    id: UUID
    code: str
    display_name: str
    field_type: FieldType
    description: str
    required: bool
    default_value: Any
    format_pattern: str | None
    min_value: float | None
    max_value: float | None
    allowed_values: list[str] | None
    table_columns: list[CatalogFieldResponse] | None
    location_hint: str
    validation_rules: list[FieldValidationRuleResponse]
    tags: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, field: CatalogField) -> CatalogFieldResponse:
        table_cols = None
        if field.table_columns:
            table_cols = [cls.from_domain(c) for c in field.table_columns]
        return cls(
            id=field.id,
            code=field.code,
            display_name=field.display_name,
            field_type=field.field_type,
            description=field.description,
            required=field.required,
            default_value=field.default_value,
            format_pattern=field.format_pattern,
            min_value=field.min_value,
            max_value=field.max_value,
            allowed_values=field.allowed_values,
            table_columns=table_cols,
            location_hint=field.location_hint,
            validation_rules=[
                FieldValidationRuleResponse(
                    rule_type=r.rule_type,
                    severity=r.severity,
                    config=r.config,
                    message=r.message,
                )
                for r in field.validation_rules
            ],
            tags=field.tags,
            is_active=field.is_active,
            created_at=field.created_at,
            updated_at=field.updated_at,
        )


# ── Validator DTOs ────────────────────────────────────────────────────


class CreateValidatorRequest(BaseModel):
    """Create a new validator in the catalog."""

    code: str = Field(min_length=2, max_length=100, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    validator_type: ValidatorType
    severity: ValidatorSeverity = ValidatorSeverity.ERROR
    config: dict[str, Any] = Field(default_factory=dict)
    applicable_natures: list[DocumentNature] = Field(default_factory=list)
    applicable_document_types: list[UUID] = Field(default_factory=list)
    applicable_fields: list[str] = Field(default_factory=list)
    visual_prompt: str = ""
    visual_expected: str = ""
    rule_expression: str = ""


class UpdateValidatorRequest(BaseModel):
    """Partial update for an existing validator."""

    name: str | None = None
    description: str | None = None
    severity: ValidatorSeverity | None = None
    config: dict[str, Any] | None = None
    applicable_natures: list[DocumentNature] | None = None
    applicable_document_types: list[UUID] | None = None
    applicable_fields: list[str] | None = None
    visual_prompt: str | None = None
    visual_expected: str | None = None
    rule_expression: str | None = None
    is_active: bool | None = None


class ValidatorResponse(BaseModel):
    """Response representation of a validator definition."""

    id: UUID
    code: str
    name: str
    description: str
    validator_type: ValidatorType
    severity: ValidatorSeverity
    config: dict[str, Any]
    applicable_natures: list[DocumentNature]
    applicable_document_types: list[UUID]
    applicable_fields: list[str]
    visual_prompt: str
    visual_expected: str
    rule_expression: str
    is_active: bool
    version: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, validator: Any) -> ValidatorResponse:
        return cls(
            id=validator.id,
            code=validator.code,
            name=validator.name,
            description=validator.description,
            validator_type=validator.validator_type,
            severity=validator.severity,
            config=validator.config,
            applicable_natures=validator.applicable_natures,
            applicable_document_types=validator.applicable_document_types,
            applicable_fields=validator.applicable_fields,
            visual_prompt=validator.visual_prompt,
            visual_expected=validator.visual_expected,
            rule_expression=validator.rule_expression,
            is_active=validator.is_active,
            version=validator.version,
            created_at=validator.created_at,
            updated_at=validator.updated_at,
        )


class ValidatorTypeInfo(BaseModel):
    """Metadata about a validator type."""

    code: str
    name: str
    description: str
    config_schema: dict[str, Any]


class TestValidatorRequest(BaseModel):
    """Test a validator against sample data."""

    sample_data: dict[str, Any]
    field_name: str | None = None


class TestValidatorResponse(BaseModel):
    """Result of testing a validator."""

    passed: bool
    message: str
    details: dict[str, Any]
    execution_time_ms: int
