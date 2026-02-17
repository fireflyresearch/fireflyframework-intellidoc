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

"""AWS S3 document storage adapter."""

from __future__ import annotations

import logging
from typing import Any

from fireflyframework_intellidoc.exceptions import StorageException

logger = logging.getLogger(__name__)


class S3DocumentStorageAdapter:
    """Stores processed document artifacts in AWS S3."""

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "intellidoc/",
        region: str = "",
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
    ) -> None:
        self._bucket = bucket
        self._prefix = prefix
        self._region = region
        self._access_key = access_key
        self._secret_key = secret_key
        self._endpoint_url = endpoint_url or None

    async def store(
        self,
        content: bytes,
        path: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        key = f"{self._prefix}{path}"
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client("s3", **self._client_kwargs()) as client:
                kwargs: dict[str, Any] = {
                    "Bucket": self._bucket,
                    "Key": key,
                    "Body": content,
                    "ContentType": content_type,
                }
                if metadata:
                    kwargs["Metadata"] = metadata
                await client.put_object(**kwargs)
            return f"s3://{self._bucket}/{key}"
        except Exception as exc:
            raise StorageException(
                f"Failed to store to S3: {exc}", code="STORAGE_WRITE_ERROR"
            ) from exc

    async def retrieve(self, reference: str) -> bytes:
        bucket, key = self._parse_ref(reference)
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client("s3", **self._client_kwargs()) as client:
                response = await client.get_object(Bucket=bucket, Key=key)
                return await response["Body"].read()
        except Exception as exc:
            raise StorageException(
                f"Failed to retrieve from S3: {exc}",
                code="STORAGE_READ_ERROR",
            ) from exc

    async def delete(self, reference: str) -> None:
        bucket, key = self._parse_ref(reference)
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client("s3", **self._client_kwargs()) as client:
                await client.delete_object(Bucket=bucket, Key=key)
        except Exception as exc:
            raise StorageException(
                f"Failed to delete from S3: {exc}",
                code="STORAGE_DELETE_ERROR",
            ) from exc

    async def exists(self, reference: str) -> bool:
        bucket, key = self._parse_ref(reference)
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client("s3", **self._client_kwargs()) as client:
                await client.head_object(Bucket=bucket, Key=key)
                return True
        except Exception:
            return False

    async def list_refs(self, prefix: str) -> list[str]:
        full_prefix = f"{self._prefix}{prefix}"
        try:
            import aioboto3

            session = aioboto3.Session()
            async with session.client("s3", **self._client_kwargs()) as client:
                response = await client.list_objects_v2(
                    Bucket=self._bucket, Prefix=full_prefix
                )
                contents = response.get("Contents", [])
                return [
                    f"s3://{self._bucket}/{item['Key']}" for item in contents
                ]
        except Exception:
            return []

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

    def _parse_ref(self, reference: str) -> tuple[str, str]:
        if reference.startswith("s3://"):
            without_scheme = reference[5:]
            parts = without_scheme.split("/", 1)
            return parts[0], parts[1] if len(parts) > 1 else ""
        return self._bucket, reference
