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

"""AWS S3 file source adapter."""

from __future__ import annotations

import mimetypes
import tempfile
from pathlib import Path
from typing import Any

from fireflyframework_intellidoc.exceptions import FileSourceException
from fireflyframework_intellidoc.types import FileReference


class S3FileSourceAdapter:
    """Reads files from AWS S3.

    Reference format: ``s3://bucket/key`` or just ``key`` with
    ``bucket`` supplied in kwargs.

    Requires the ``aioboto3`` package (optional dependency).
    """

    def __init__(
        self,
        *,
        region: str = "",
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
        temp_dir: str | None = None,
    ) -> None:
        self._region = region
        self._access_key = access_key
        self._secret_key = secret_key
        self._endpoint_url = endpoint_url or None
        self._temp_dir = temp_dir
        self._session: Any = None

    @property
    def source_type(self) -> str:
        return "s3"

    async def read(self, reference: str, **kwargs: Any) -> FileReference:
        bucket, key = self._parse_reference(reference, kwargs)
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client(
                "s3", **self._client_kwargs()
            ) as client:
                response = await client.get_object(Bucket=bucket, Key=key)
                body = await response["Body"].read()

                filename = Path(key).name
                mime_type, _ = mimetypes.guess_type(filename)
                suffix = Path(filename).suffix or ""
                fd, temp_path = tempfile.mkstemp(
                    suffix=suffix, dir=self._temp_dir
                )
                with open(fd, "wb") as f:
                    f.write(body)

                return FileReference(
                    source_type="s3",
                    source_reference=reference,
                    filename=filename,
                    mime_type=mime_type or response.get(
                        "ContentType", "application/octet-stream"
                    ),
                    file_size_bytes=len(body),
                    content_path=Path(temp_path),
                )
        except Exception as exc:
            raise FileSourceException("s3", reference, str(exc)) from exc

    async def exists(self, reference: str, **kwargs: Any) -> bool:
        bucket, key = self._parse_reference(reference, kwargs)
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client(
                "s3", **self._client_kwargs()
            ) as client:
                await client.head_object(Bucket=bucket, Key=key)
                return True
        except Exception:
            return False

    async def metadata(self, reference: str, **kwargs: Any) -> dict[str, Any]:
        bucket, key = self._parse_reference(reference, kwargs)
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client(
                "s3", **self._client_kwargs()
            ) as client:
                response = await client.head_object(Bucket=bucket, Key=key)
                return {
                    "filename": Path(key).name,
                    "size_bytes": response.get("ContentLength", 0),
                    "mime_type": response.get(
                        "ContentType", "application/octet-stream"
                    ),
                    "last_modified": str(response.get("LastModified", "")),
                }
        except Exception as exc:
            raise FileSourceException("s3", reference, str(exc)) from exc

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    def _client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self._region:
            kwargs["region_name"] = self._region
        if self._access_key and self._secret_key:
            kwargs["aws_access_key_id"] = self._access_key
            kwargs["aws_secret_access_key"] = self._secret_key
        if self._endpoint_url:
            kwargs["endpoint_url"] = self._endpoint_url
        return kwargs

    @staticmethod
    def _parse_reference(
        reference: str, kwargs: dict[str, Any]
    ) -> tuple[str, str]:
        if reference.startswith("s3://"):
            without_scheme = reference[5:]
            parts = without_scheme.split("/", 1)
            if len(parts) != 2:
                raise FileSourceException(
                    "s3", reference, "Invalid S3 URI format. Expected s3://bucket/key"
                )
            return parts[0], parts[1]

        bucket = kwargs.get("bucket", "")
        if not bucket:
            raise FileSourceException(
                "s3",
                reference,
                "Bucket must be provided in kwargs or use s3://bucket/key format",
            )
        return bucket, reference
