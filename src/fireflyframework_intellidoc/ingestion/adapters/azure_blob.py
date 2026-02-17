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

"""Azure Blob Storage file source adapter."""

from __future__ import annotations

import mimetypes
import tempfile
from pathlib import Path
from typing import Any

from fireflyframework_intellidoc.exceptions import FileSourceException
from fireflyframework_intellidoc.types import FileReference


class AzureBlobFileSourceAdapter:
    """Reads files from Azure Blob Storage.

    Reference format: ``container/blob_name`` or just ``blob_name``
    with ``container`` supplied in kwargs.

    Requires the ``azure-storage-blob`` package (optional dependency).
    """

    def __init__(
        self,
        *,
        connection_string: str = "",
        account_url: str = "",
        temp_dir: str | None = None,
    ) -> None:
        self._connection_string = connection_string
        self._account_url = account_url
        self._temp_dir = temp_dir
        self._client: Any = None

    @property
    def source_type(self) -> str:
        return "azure_blob"

    async def read(self, reference: str, **kwargs: Any) -> FileReference:
        container, blob_name = self._parse_reference(reference, kwargs)
        try:
            client = await self._get_client()
            container_client = client.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)

            downloader = await blob_client.download_blob()
            content = await downloader.readall()

            filename = Path(blob_name).name
            mime_type, _ = mimetypes.guess_type(filename)
            suffix = Path(filename).suffix or ""
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix, dir=self._temp_dir
            )
            with open(fd, "wb") as f:
                f.write(content)

            return FileReference(
                source_type="azure_blob",
                source_reference=reference,
                filename=filename,
                mime_type=mime_type or "application/octet-stream",
                file_size_bytes=len(content),
                content_path=Path(temp_path),
            )
        except Exception as exc:
            raise FileSourceException(
                "azure_blob", reference, str(exc)
            ) from exc

    async def exists(self, reference: str, **kwargs: Any) -> bool:
        container, blob_name = self._parse_reference(reference, kwargs)
        try:
            client = await self._get_client()
            container_client = client.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            await blob_client.get_blob_properties()
            return True
        except Exception:
            return False

    async def metadata(self, reference: str, **kwargs: Any) -> dict[str, Any]:
        container, blob_name = self._parse_reference(reference, kwargs)
        try:
            client = await self._get_client()
            container_client = client.get_container_client(container)
            blob_client = container_client.get_blob_client(blob_name)
            props = await blob_client.get_blob_properties()
            return {
                "filename": Path(blob_name).name,
                "size_bytes": props.size,
                "mime_type": props.content_settings.content_type
                or "application/octet-stream",
                "last_modified": str(props.last_modified),
            }
        except Exception as exc:
            raise FileSourceException(
                "azure_blob", reference, str(exc)
            ) from exc

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

    @staticmethod
    def _parse_reference(
        reference: str, kwargs: dict[str, Any]
    ) -> tuple[str, str]:
        container = kwargs.get("container", "")
        if "/" in reference and not container:
            parts = reference.split("/", 1)
            return parts[0], parts[1]
        if not container:
            raise FileSourceException(
                "azure_blob",
                reference,
                "Container must be provided in kwargs or use container/blob format",
            )
        return container, reference
