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

"""HTTP/HTTPS URL file source adapter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from fireflyframework_intellidoc.exceptions import FileSourceException
from fireflyframework_intellidoc.types import FileReference


class UrlFileSourceAdapter:
    """Downloads files from HTTP/HTTPS URLs."""

    def __init__(
        self,
        *,
        timeout: float = 60.0,
        temp_dir: str | None = None,
    ) -> None:
        self._timeout = timeout
        self._temp_dir = temp_dir
        self._client: httpx.AsyncClient | None = None

    @property
    def source_type(self) -> str:
        return "url"

    async def read(self, reference: str, **kwargs: Any) -> FileReference:
        headers = kwargs.get("headers", {})
        client = self._ensure_client()

        try:
            response = await client.get(
                reference, headers=headers, follow_redirects=True
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FileSourceException("url", reference, str(exc)) from exc

        filename = self._extract_filename(reference, response)
        content_type = response.headers.get(
            "content-type", "application/octet-stream"
        ).split(";")[0].strip()

        temp_path = self._save_to_temp(response.content, filename)

        return FileReference(
            source_type="url",
            source_reference=reference,
            filename=filename,
            mime_type=content_type,
            file_size_bytes=len(response.content),
            content_path=temp_path,
        )

    async def exists(self, reference: str, **kwargs: Any) -> bool:
        headers = kwargs.get("headers", {})
        client = self._ensure_client()
        try:
            response = await client.head(
                reference, headers=headers, follow_redirects=True
            )
            return response.is_success
        except httpx.HTTPError:
            return False

    async def metadata(self, reference: str, **kwargs: Any) -> dict[str, Any]:
        headers = kwargs.get("headers", {})
        client = self._ensure_client()
        try:
            response = await client.head(
                reference, headers=headers, follow_redirects=True
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FileSourceException("url", reference, str(exc)) from exc

        content_length = response.headers.get("content-length", "0")
        return {
            "filename": self._extract_filename(reference, response),
            "size_bytes": int(content_length),
            "mime_type": response.headers.get(
                "content-type", "application/octet-stream"
            ),
        }

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=self._timeout)

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    def _save_to_temp(self, content: bytes, filename: str) -> Path:
        suffix = Path(filename).suffix or ""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self._temp_dir)
        with open(fd, "wb") as f:
            f.write(content)
        return Path(path)

    @staticmethod
    def _extract_filename(url: str, response: httpx.Response) -> str:
        cd = response.headers.get("content-disposition", "")
        if "filename=" in cd:
            parts = cd.split("filename=")
            return parts[1].strip().strip('"').strip("'")

        parsed = urlparse(url)
        path_name = Path(unquote(parsed.path)).name
        return path_name if path_name and "." in path_name else "download"
