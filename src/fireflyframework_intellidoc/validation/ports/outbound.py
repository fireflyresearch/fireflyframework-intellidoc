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

"""Outbound ports for document validation.

:class:`ValidatorPort` abstracts individual validator execution
so that the validation engine remains agnostic to how each
validator type is implemented (regex, VLM call, expression eval, etc.).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from fireflyframework_intellidoc.catalog.domain.validator_definition import (
    ValidatorDefinition,
)
from fireflyframework_intellidoc.results.domain.processing_result import (
    ValidationResult,
)
from fireflyframework_intellidoc.types import PageImage, ValidatorType


@runtime_checkable
class ValidatorPort(Protocol):
    """Port for individual validator execution."""

    @property
    def validator_type(self) -> ValidatorType:
        """The type of validation this port handles."""
        ...

    async def validate(
        self,
        data: dict[str, Any],
        definition: ValidatorDefinition,
        *,
        pages: list[PageImage] | None = None,
    ) -> ValidationResult:
        """Execute validation against the extracted data."""
        ...
