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

"""Local filesystem document storage adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from fireflyframework_intellidoc.exceptions import StorageException

logger = logging.getLogger(__name__)


class LocalDocumentStorageAdapter:
    """Stores processed document artifacts on the local filesystem."""

    def __init__(self, base_path: str = "/var/intellidoc/storage") -> None:
        self._base = Path(base_path)

    async def store(
        self,
        content: bytes,
        path: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        full_path = self._base / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        logger.debug("Stored %d bytes at %s", len(content), full_path)
        return str(full_path)

    async def retrieve(self, reference: str) -> bytes:
        path = Path(reference)
        if not path.exists():
            raise StorageException(
                f"File not found: {reference}", code="STORAGE_NOT_FOUND"
            )
        return path.read_bytes()

    async def delete(self, reference: str) -> None:
        path = Path(reference)
        if path.exists():
            path.unlink()

    async def exists(self, reference: str) -> bool:
        return Path(reference).exists()

    async def list_refs(self, prefix: str) -> list[str]:
        base = self._base / prefix
        if not base.exists():
            return []
        return [str(p) for p in base.rglob("*") if p.is_file()]

    async def start(self) -> None:
        self._base.mkdir(parents=True, exist_ok=True)

    async def stop(self) -> None:
        pass
