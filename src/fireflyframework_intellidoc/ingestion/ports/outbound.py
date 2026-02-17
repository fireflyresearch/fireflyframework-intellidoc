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

"""Outbound ports for file ingestion.

:class:`FileSourcePort` abstracts the mechanism used to read files
from various backends (local disk, HTTP URLs, S3, Azure Blob, GCS).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from fireflyframework_intellidoc.types import FileReference


@runtime_checkable
class FileSourcePort(Protocol):
    """Port for reading files from various sources."""

    @property
    def source_type(self) -> str:
        """Identifier for this source type (e.g., 'local', 's3', 'url')."""
        ...

    async def read(self, reference: str, **kwargs: Any) -> FileReference:
        """Read a file from the source and return a normalized reference.

        The returned :class:`FileReference` will have ``content_path``
        pointing to a local temporary copy of the file.
        """
        ...

    async def exists(self, reference: str, **kwargs: Any) -> bool:
        """Check if the file exists at the source."""
        ...

    async def metadata(self, reference: str, **kwargs: Any) -> dict[str, Any]:
        """Get file metadata without downloading content."""
        ...

    async def start(self) -> None:
        """Initialize the adapter (e.g., establish connections)."""
        ...

    async def stop(self) -> None:
        """Clean up resources."""
        ...
