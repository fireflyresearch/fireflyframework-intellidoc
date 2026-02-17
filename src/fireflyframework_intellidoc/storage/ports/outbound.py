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

"""Outbound ports for document artifact storage.

:class:`DocumentStoragePort` abstracts the persistence of processed
document artifacts (enhanced images, split pages, etc.) to various
backends such as local filesystem, S3, Azure Blob, or GCS.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentStoragePort(Protocol):
    """Port for storing processed document artifacts."""

    async def store(
        self,
        content: bytes,
        path: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Store content and return a reference key/URL."""
        ...

    async def retrieve(self, reference: str) -> bytes:
        """Retrieve stored content by reference."""
        ...

    async def delete(self, reference: str) -> None:
        """Delete stored content."""
        ...

    async def exists(self, reference: str) -> bool:
        """Check if content exists."""
        ...

    async def list_refs(self, prefix: str) -> list[str]:
        """List references matching a prefix."""
        ...

    async def start(self) -> None:
        """Initialize the adapter."""
        ...

    async def stop(self) -> None:
        """Clean up resources."""
        ...
