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

"""Catalog field domain model.

A :class:`CatalogField` is a reusable, self-describing field definition
stored in the fields catalog.  Each field carries its own embedded
:class:`FieldValidationRule` entries so that simple validation logic
travels with the field rather than requiring separate validator setup.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.types import (
    FieldType,
    ValidatorSeverity,
    ValidatorType,
)


class FieldValidationRule(BaseModel):
    """An embedded validation rule on a catalog field.

    Reuses the same :class:`ValidatorType` and :class:`ValidatorSeverity`
    enums as the standalone :class:`ValidatorDefinition`, allowing
    field-level rules to share the same validation engine.
    """

    rule_type: ValidatorType
    severity: ValidatorSeverity = ValidatorSeverity.ERROR
    config: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class CatalogField(BaseModel):
    """A reusable field definition in the fields catalog.

    Combines all properties previously found in ``FieldDefinition``
    with catalog-level metadata (``id``, ``code``, ``tags``) and
    embedded validation rules.
    """

    id: UUID = Field(default_factory=uuid4)
    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")

    display_name: str
    field_type: FieldType
    description: str = ""
    required: bool = False
    default_value: Any = None

    # Validation hints
    format_pattern: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[str] | None = None

    # Table-specific (self-referencing for column definitions)
    table_columns: list[CatalogField] | None = None

    # Location hints
    location_hint: str = ""

    # Embedded validation rules
    validation_rules: list[FieldValidationRule] = Field(default_factory=list)

    # Catalog metadata
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
