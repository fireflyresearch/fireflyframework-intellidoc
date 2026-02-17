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

"""Azure Blob Storage document storage adapter."""

from __future__ import annotations

import logging
from typing import Any

from fireflyframework_intellidoc.exceptions import StorageException

logger = logging.getLogger(__name__)


class AzureBlobDocumentStorageAdapter:
    """Stores processed document artifacts in Azure Blob Storage."""

    def __init__(
        self,
        *,
        container_name: str,
        connection_string: str = "",
        account_url: str = "",
        prefix: str = "intellidoc/",
    ) -> None:
        self._container_name = container_name
        self._connection_string = connection_string
        self._account_url = account_url
        self._prefix = prefix
        self._client: Any = None

    async def store(
        self,
        content: bytes,
        path: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        blob_name = f"{self._prefix}{path}"
        try:
            client = await self._get_client()
            container_client = client.get_container_client(self._container_name)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.upload_blob(
                content,
                content_settings=self._content_settings(content_type),
                metadata=metadata,
                overwrite=True,
            )
            return f"{self._container_name}/{blob_name}"
        except Exception as exc:
            raise StorageException(
                f"Failed to store to Azure Blob: {exc}",
                code="STORAGE_WRITE_ERROR",
            ) from exc

    async def retrieve(self, reference: str) -> bytes:
        container, blob_name = self._parse_ref(reference)
        try:
            client = await self._get_client()
            container_client = client.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            downloader = await blob_client.download_blob()
            return await downloader.readall()
        except Exception as exc:
            raise StorageException(
                f"Failed to retrieve from Azure Blob: {exc}",
                code="STORAGE_READ_ERROR",
            ) from exc

    async def delete(self, reference: str) -> None:
        container, blob_name = self._parse_ref(reference)
        try:
            client = await self._get_client()
            container_client = client.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.delete_blob()
        except Exception as exc:
            raise StorageException(
                f"Failed to delete from Azure Blob: {exc}",
                code="STORAGE_DELETE_ERROR",
            ) from exc

    async def exists(self, reference: str) -> bool:
        container, blob_name = self._parse_ref(reference)
        try:
            client = await self._get_client()
            container_client = client.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.get_blob_properties()
            return True
        except Exception:
            return False

    async def list_refs(self, prefix: str) -> list[str]:
        full_prefix = f"{self._prefix}{prefix}"
        try:
            client = await self._get_client()
            container_client = client.get_container_client(self._container_name)
            refs: list[str] = []
            async for blob in container_client.list_blobs(name_starts_with=full_prefix):
                refs.append(f"{self._container_name}/{blob.name}")
            return refs
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
            from azure.storage.blob.aio import BlobServiceClient

            if self._connection_string:
                self._client = BlobServiceClient.from_connection_string(
                    self._connection_string
                )
            else:
                self._client = BlobServiceClient(self._account_url)
        return self._client

    def _parse_ref(self, reference: str) -> tuple[str, str]:
        if "/" in reference:
            parts = reference.split("/", 1)
            return parts[0], parts[1]
        return self._container_name, reference

    @staticmethod
    def _content_settings(content_type: str) -> Any:
        from azure.storage.blob import ContentSettings

        return ContentSettings(content_type=content_type)
