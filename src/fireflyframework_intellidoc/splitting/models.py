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

"""Splitting result models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.types import DocumentBoundary


class SplittingResult(BaseModel):
    """Result of document boundary detection."""

    boundaries: list[DocumentBoundary] = Field(default_factory=list)
    total_documents_detected: int = 0
    total_pages: int = 0
    strategy_used: str = ""
    confidence: float = 1.0
