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

"""Outbound ports for document splitting.

:class:`DocumentSplitterPort` abstracts the strategy used to detect
document boundaries within multi-document files.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from fireflyframework_intellidoc.splitting.models import SplittingResult
from fireflyframework_intellidoc.types import PageImage


@runtime_checkable
class DocumentSplitterPort(Protocol):
    """Port for document boundary detection."""

    @property
    def strategy_name(self) -> str:
        """Name of the splitting strategy (e.g., 'visual', 'page_based')."""
        ...

    async def detect_boundaries(
        self,
        pages: list[PageImage],
        **kwargs: Any,
    ) -> SplittingResult:
        """Detect document boundaries in a sequence of page images."""
        ...
