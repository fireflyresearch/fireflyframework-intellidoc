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

"""Classification result models."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ClassificationCandidate(BaseModel):
    """A single classification candidate with confidence."""

    document_type_id: UUID
    document_type_code: str
    confidence: float
    reasoning: str = ""


class ClassificationResult(BaseModel):
    """Result of document classification."""

    best_match: ClassificationCandidate | None = None
    candidates: list[ClassificationCandidate] = Field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
