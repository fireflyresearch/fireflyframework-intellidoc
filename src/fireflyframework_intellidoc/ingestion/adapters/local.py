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

"""Local filesystem file source adapter."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from fireflyframework_intellidoc.exceptions import FileSourceException
from fireflyframework_intellidoc.types import FileReference


class LocalFileSourceAdapter:
    """Reads files from the local filesystem."""

    @property
    def source_type(self) -> str:
        return "local"

    async def read(self, reference: str, **kwargs: Any) -> FileReference:
        path = Path(reference)
        if not path.exists():
            raise FileSourceException("local", reference, "File not found")
        if not path.is_file():
            raise FileSourceException("local", reference, "Not a file")

        mime_type, _ = mimetypes.guess_type(path.name)
        return FileReference(
            source_type="local",
            source_reference=reference,
            filename=path.name,
            mime_type=mime_type or "application/octet-stream",
            file_size_bytes=path.stat().st_size,
            content_path=path,
        )

    async def exists(self, reference: str, **kwargs: Any) -> bool:
        return Path(reference).is_file()

    async def metadata(self, reference: str, **kwargs: Any) -> dict[str, Any]:
        path = Path(reference)
        if not path.exists():
            raise FileSourceException("local", reference, "File not found")
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(path.name)
        return {
            "filename": path.name,
            "size_bytes": stat.st_size,
            "mime_type": mime_type or "application/octet-stream",
            "modified_at": stat.st_mtime,
        }

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass
