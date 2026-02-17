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

"""CLI-specific auto-configuration.

Provides in-memory catalog and result storage adapters when
running in CLI mode (no database), and the branded shell adapter.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from pyfly.container.bean import bean
from pyfly.context.conditions import (
    auto_configuration,
    conditional_on_missing_bean,
    conditional_on_property,
)
from pyfly.shell.ports.outbound import ShellRunnerPort

from fireflyframework_intellidoc.catalog.adapters.memory import (
    InMemoryDocumentTypeCatalog,
    InMemoryFieldCatalog,
    InMemoryValidatorCatalog,
)
from fireflyframework_intellidoc.catalog.loader import CatalogLoader
from fireflyframework_intellidoc.catalog.ports.outbound import (
    DocumentTypeCatalogPort,
    FieldCatalogPort,
    ValidatorCatalogPort,
)
from fireflyframework_intellidoc.cli.shell_adapter import IntelliDocShellAdapter
from fireflyframework_intellidoc.results.adapters.memory import InMemoryResultStorage
from fireflyframework_intellidoc.results.ports.outbound import ResultStoragePort

logger = logging.getLogger(__name__)


@auto_configuration
@conditional_on_property("pyfly.shell.enabled", having_value="true")
class IntelliDocCLIAutoConfiguration:
    """Auto-configuration for CLI mode — in-memory adapters and branded shell."""

    def __init__(self) -> None:
        self._doc_types = InMemoryDocumentTypeCatalog()
        self._fields = InMemoryFieldCatalog()
        self._validators = InMemoryValidatorCatalog()

        # Load catalog YAML if present in CWD
        catalog_path = Path.cwd() / "catalog.yaml"
        if catalog_path.exists():
            loader = CatalogLoader(self._doc_types, self._fields, self._validators)
            try:
                asyncio.get_event_loop().run_until_complete(loader.load(catalog_path))
                logger.info("Loaded catalog from %s", catalog_path)
            except Exception:
                logger.debug("No event loop; catalog will be loaded lazily")

    # ── Shell Adapter ────────────────────────────────────────────────

    @bean
    def shell_runner(self) -> ShellRunnerPort:
        return IntelliDocShellAdapter()

    # ── In-Memory Catalog Ports ──────────────────────────────────────

    @bean
    @conditional_on_missing_bean(DocumentTypeCatalogPort)
    def document_type_catalog(self) -> DocumentTypeCatalogPort:
        return self._doc_types  # type: ignore[return-value]

    @bean
    @conditional_on_missing_bean(FieldCatalogPort)
    def field_catalog(self) -> FieldCatalogPort:
        return self._fields  # type: ignore[return-value]

    @bean
    @conditional_on_missing_bean(ValidatorCatalogPort)
    def validator_catalog(self) -> ValidatorCatalogPort:
        return self._validators  # type: ignore[return-value]

    # ── In-Memory Result Storage ─────────────────────────────────────

    @bean
    @conditional_on_missing_bean(ResultStoragePort)
    def result_storage(self) -> ResultStoragePort:
        return InMemoryResultStorage()  # type: ignore[return-value]
