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

"""Google Cloud Storage file source adapter."""

from __future__ import annotations

import mimetypes
import tempfile
from pathlib import Path
from typing import Any

from fireflyframework_intellidoc.exceptions import FileSourceException
from fireflyframework_intellidoc.types import FileReference


class GCSFileSourceAdapter:
    """Reads files from Google Cloud Storage.

    Reference format: ``gs://bucket/object`` or just ``object``
    with ``bucket`` supplied in kwargs.

    Requires the ``gcloud-aio-storage`` package (optional dependency).
    """

    def __init__(
        self,
        *,
        project_id: str = "",
        credentials_path: str = "",
        temp_dir: str | None = None,
    ) -> None:
        self._project_id = project_id
        self._credentials_path = credentials_path
        self._temp_dir = temp_dir
        self._client: Any = None

    @property
    def source_type(self) -> str:
        return "gcs"

    async def read(self, reference: str, **kwargs: Any) -> FileReference:
        bucket, object_name = self._parse_reference(reference, kwargs)
        try:
            client = await self._get_client()
            content = await client.download(bucket, object_name)

            filename = Path(object_name).name
            mime_type, _ = mimetypes.guess_type(filename)
            suffix = Path(filename).suffix or ""
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix, dir=self._temp_dir
            )
            with open(fd, "wb") as f:
                f.write(content)

            return FileReference(
                source_type="gcs",
                source_reference=reference,
                filename=filename,
                mime_type=mime_type or "application/octet-stream",
                file_size_bytes=len(content),
                content_path=Path(temp_path),
            )
        except Exception as exc:
            raise FileSourceException("gcs", reference, str(exc)) from exc

    async def exists(self, reference: str, **kwargs: Any) -> bool:
        bucket, object_name = self._parse_reference(reference, kwargs)
        try:
            client = await self._get_client()
            objects = await client.list_objects(bucket, params={"prefix": object_name})
            return any(
                item.get("name") == object_name
                for item in objects.get("items", [])
            )
        except Exception:
            return False

    async def metadata(self, reference: str, **kwargs: Any) -> dict[str, Any]:
        bucket, object_name = self._parse_reference(reference, kwargs)
        try:
            client = await self._get_client()
            metadata = await client.download_metadata(bucket, object_name)
            return {
                "filename": Path(object_name).name,
                "size_bytes": int(metadata.get("size", 0)),
                "mime_type": metadata.get(
                    "contentType", "application/octet-stream"
                ),
                "last_modified": metadata.get("updated", ""),
            }
        except Exception as exc:
            raise FileSourceException("gcs", reference, str(exc)) from exc

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

    @staticmethod
    def _parse_reference(
        reference: str, kwargs: dict[str, Any]
    ) -> tuple[str, str]:
        if reference.startswith("gs://"):
            without_scheme = reference[5:]
            parts = without_scheme.split("/", 1)
            if len(parts) != 2:
                raise FileSourceException(
                    "gcs",
                    reference,
                    "Invalid GCS URI format. Expected gs://bucket/object",
                )
            return parts[0], parts[1]

        bucket = kwargs.get("bucket", "")
        if not bucket:
            raise FileSourceException(
                "gcs",
                reference,
                "Bucket must be provided in kwargs or use gs://bucket/object format",
            )
        return bucket, reference
