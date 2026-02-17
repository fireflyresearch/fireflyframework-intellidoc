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

"""Document type domain model.

A :class:`DocumentType` defines a category of document in the catalog,
including how the document looks visually, what data to extract from it,
and which validators apply to it.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.types import DocumentNature


class DocumentType(BaseModel):
    """A registered document type in the catalog.

    Defines what a document looks like, what data to extract,
    and how to validate it.  Instances are created and managed
    through the catalog management API.
    """

    id: UUID = Field(default_factory=uuid4)
    code: str
    name: str
    description: str
    nature: DocumentNature

    # Visual identification
    visual_description: str = ""
    visual_cues: list[str] = Field(default_factory=list)
    sample_keywords: list[str] = Field(default_factory=list)

    # Classification
    classification_instructions: str = ""
    classification_confidence_threshold: float = 0.7

    # Extraction
    default_field_codes: list[str] = Field(default_factory=list)
    extraction_instructions: str = ""

    # Validation
    validator_ids: list[UUID] = Field(default_factory=list)

    # Metadata
    version: str = "1.0.0"
    is_active: bool = True
    tags: list[str] = Field(default_factory=list)
    supported_languages: list[str] = Field(default_factory=lambda: ["en"])

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
