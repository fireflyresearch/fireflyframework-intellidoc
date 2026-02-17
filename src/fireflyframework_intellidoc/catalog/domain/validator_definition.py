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

"""Validator definition domain model.

A :class:`ValidatorDefinition` is a reusable validation rule stored
in the catalog.  Validators can be linked to specific document natures,
document types, or individual fields and are executed after data
extraction to verify correctness.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.types import (
    DocumentNature,
    ValidatorSeverity,
    ValidatorType,
)


class ValidatorDefinition(BaseModel):
    """A reusable validator definition in the catalog."""

    id: UUID = Field(default_factory=uuid4)
    code: str
    name: str
    description: str = ""
    validator_type: ValidatorType
    severity: ValidatorSeverity = ValidatorSeverity.ERROR

    # Configuration
    config: dict[str, Any] = Field(default_factory=dict)

    # Applicability
    applicable_natures: list[DocumentNature] = Field(default_factory=list)
    applicable_document_types: list[UUID] = Field(default_factory=list)
    applicable_fields: list[str] = Field(default_factory=list)

    # Visual validator config
    visual_prompt: str = ""
    visual_expected: str = ""

    # Business rule config
    rule_expression: str = ""

    is_active: bool = True
    version: str = "1.0.0"

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
