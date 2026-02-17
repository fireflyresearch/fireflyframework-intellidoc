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

"""Ingestion application service.

:class:`IngestionService` acts as a multi-adapter registry, dispatching
file read requests to the appropriate :class:`FileSourcePort` adapter
based on the ``source_type`` identifier.
"""

from __future__ import annotations

import logging
from typing import Any

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.exceptions import (
    FileSourceException,
    FileTooLargeException,
    UnsupportedFileTypeException,
)
from fireflyframework_intellidoc.ingestion.ports.outbound import FileSourcePort
from fireflyframework_intellidoc.types import FileReference

logger = logging.getLogger(__name__)


@service
class IngestionService:
    """Coordinates file ingestion from multiple source adapters."""

    def __init__(
        self,
        config: IntelliDocConfig,
        file_sources: list[FileSourcePort],
    ) -> None:
        self._config = config
        self._sources: dict[str, FileSourcePort] = {}
        for source in file_sources:
            self._sources[source.source_type] = source

    async def ingest(
        self,
        source_type: str,
        reference: str,
        **kwargs: Any,
    ) -> FileReference:
        """Ingest a file from the given source.

        Validates the source type, downloads the file, checks the MIME
        type and file size limits, then returns a normalized
        :class:`FileReference`.
        """
        adapter = self._get_adapter(source_type)

        logger.info(
            "Ingesting file from %s: %s", source_type, reference
        )
        file_ref = await adapter.read(reference, **kwargs)

        self._validate_mime_type(file_ref)
        self._validate_file_size(file_ref)

        logger.info(
            "Ingested %s (%s, %d bytes)",
            file_ref.filename,
            file_ref.mime_type,
            file_ref.file_size_bytes,
        )
        return file_ref

    async def check_exists(
        self,
        source_type: str,
        reference: str,
        **kwargs: Any,
    ) -> bool:
        adapter = self._get_adapter(source_type)
        return await adapter.exists(reference, **kwargs)

    async def get_metadata(
        self,
        source_type: str,
        reference: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        adapter = self._get_adapter(source_type)
        return await adapter.metadata(reference, **kwargs)

    @property
    def available_sources(self) -> list[str]:
        return list(self._sources.keys())

    def _get_adapter(self, source_type: str) -> FileSourcePort:
        adapter = self._sources.get(source_type)
        if adapter is None:
            available = ", ".join(self._sources.keys()) or "none"
            raise FileSourceException(
                source_type,
                "",
                f"No adapter registered for source type '{source_type}'. "
                f"Available: {available}",
            )
        return adapter

    def _validate_mime_type(self, file_ref: FileReference) -> None:
        if file_ref.mime_type not in self._config.supported_mime_types:
            raise UnsupportedFileTypeException(file_ref.mime_type)

    def _validate_file_size(self, file_ref: FileReference) -> None:
        max_bytes = self._config.max_file_size_mb * 1024 * 1024
        if file_ref.file_size_bytes > max_bytes:
            file_size_mb = file_ref.file_size_bytes / (1024 * 1024)
            raise FileTooLargeException(
                file_size_mb, float(self._config.max_file_size_mb)
            )
