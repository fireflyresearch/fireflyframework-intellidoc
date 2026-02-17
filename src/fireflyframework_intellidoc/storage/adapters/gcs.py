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

"""Google Cloud Storage document storage adapter."""

from __future__ import annotations

import logging
from typing import Any

from fireflyframework_intellidoc.exceptions import StorageException

logger = logging.getLogger(__name__)


class GCSDocumentStorageAdapter:
    """Stores processed document artifacts in Google Cloud Storage."""

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "intellidoc/",
    ) -> None:
        self._bucket = bucket
        self._prefix = prefix
        self._client: Any = None

    async def store(
        self,
        content: bytes,
        path: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        object_name = f"{self._prefix}{path}"
        try:
            client = await self._get_client()
            await client.upload(
                self._bucket,
                object_name,
                content,
                metadata=metadata,
            )
            return f"gs://{self._bucket}/{object_name}"
        except Exception as exc:
            raise StorageException(
                f"Failed to store to GCS: {exc}",
                code="STORAGE_WRITE_ERROR",
            ) from exc

    async def retrieve(self, reference: str) -> bytes:
        bucket, object_name = self._parse_ref(reference)
        try:
            client = await self._get_client()
            return await client.download(bucket, object_name)
        except Exception as exc:
            raise StorageException(
                f"Failed to retrieve from GCS: {exc}",
                code="STORAGE_READ_ERROR",
            ) from exc

    async def delete(self, reference: str) -> None:
        bucket, object_name = self._parse_ref(reference)
        try:
            client = await self._get_client()
            await client.delete(bucket, object_name)
        except Exception as exc:
            raise StorageException(
                f"Failed to delete from GCS: {exc}",
                code="STORAGE_DELETE_ERROR",
            ) from exc

    async def exists(self, reference: str) -> bool:
        bucket, object_name = self._parse_ref(reference)
        try:
            client = await self._get_client()
            objects = await client.list_objects(
                bucket, params={"prefix": object_name}
            )
            return any(
                item.get("name") == object_name
                for item in objects.get("items", [])
            )
        except Exception:
            return False

    async def list_refs(self, prefix: str) -> list[str]:
        full_prefix = f"{self._prefix}{prefix}"
        try:
            client = await self._get_client()
            objects = await client.list_objects(
                self._bucket, params={"prefix": full_prefix}
            )
            return [
                f"gs://{self._bucket}/{item['name']}"
                for item in objects.get("items", [])
            ]
        except Exception:
            return []

    async def start(self) -> None:
        await self._get_client()

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def _get_client(self) -> Any:
        if self._client is None:
            from gcloud.aio.storage import Storage

            self._client = Storage()
        return self._client

    def _parse_ref(self, reference: str) -> tuple[str, str]:
        if reference.startswith("gs://"):
            without_scheme = reference[5:]
            parts = without_scheme.split("/", 1)
            return parts[0], parts[1] if len(parts) > 1 else ""
        return self._bucket, reference
