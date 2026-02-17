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

"""Outbound ports for document classification.

:class:`ClassifierPort` abstracts the VLM-powered classification
of document pages against the catalog of known document types.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from fireflyframework_intellidoc.catalog.domain.document_type import DocumentType
from fireflyframework_intellidoc.classification.models import ClassificationResult
from fireflyframework_intellidoc.types import DocumentNature, PageImage


@runtime_checkable
class ClassifierPort(Protocol):
    """Port for document classification."""

    async def classify(
        self,
        pages: list[PageImage],
        available_types: list[DocumentType],
        *,
        expected_type: str | None = None,
        expected_nature: DocumentNature | None = None,
    ) -> ClassificationResult:
        """Classify document pages against available document types."""
        ...
