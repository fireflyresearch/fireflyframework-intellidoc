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

"""Catalog management commands for the IntelliDoc CLI.

Defines ``catalog validate`` and ``catalog show`` as ``@shell_component``
commands in the ``catalog`` group.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pyfly.container.stereotypes import shell_component
from pyfly.shell.decorators import shell_method, shell_option
from rich.table import Table

from fireflyframework_intellidoc.catalog.adapters.memory import (
    InMemoryDocumentTypeCatalog,
    InMemoryFieldCatalog,
    InMemoryValidatorCatalog,
)
from fireflyframework_intellidoc.catalog.loader import CatalogLoader
from fireflyframework_intellidoc.cli.banner import console


@shell_component
class CatalogCommands:
    """Catalog management commands."""

    @shell_method(key="validate", help="Validate a catalog YAML file", group="catalog")
    async def validate(self, file: str) -> None:
        """Parse and validate a catalog YAML file without processing."""
        path = Path(file)
        if not path.exists():
            console.print(f"  [error]✗[/error] File not found: {file}")
            sys.exit(1)

        try:
            loader = CatalogLoader(
                InMemoryDocumentTypeCatalog(),
                InMemoryFieldCatalog(),
                InMemoryValidatorCatalog(),
            )
            counts = await loader.load(path)

            console.print(f"  [success]✓[/success] Catalog is valid: {path.name}")
            console.print(f"    Document types: {counts['document_types']}")
            console.print(f"    Fields:         {counts['fields']}")
            console.print(f"    Validators:     {counts['validators']}")

        except Exception as exc:
            console.print(f"  [error]✗[/error] Invalid catalog: {exc}")
            sys.exit(1)

    @shell_method(key="show", help="Display catalog contents", group="catalog")
    @shell_option("format", help="Output format: table, json", default="table")
    async def show(self, file: str, format: str = "table") -> None:
        """Load and display contents of a catalog YAML file."""
        path = Path(file)
        if not path.exists():
            console.print(f"  [error]✗[/error] File not found: {file}")
            sys.exit(1)

        doc_types_cat = InMemoryDocumentTypeCatalog()
        fields_cat = InMemoryFieldCatalog()
        validators_cat = InMemoryValidatorCatalog()

        try:
            loader = CatalogLoader(doc_types_cat, fields_cat, validators_cat)
            await loader.load(path)
        except Exception as exc:
            console.print(f"  [error]✗[/error] Failed to load catalog: {exc}")
            sys.exit(1)

        if format == "json":
            import json

            doc_types = await doc_types_cat.find_all_active()
            fields, _ = await fields_cat.find_all()
            validators, _ = await validators_cat.find_all()

            data = {
                "document_types": [dt.model_dump(mode="json") for dt in doc_types],
                "fields": [f.model_dump(mode="json") for f in fields],
                "validators": [v.model_dump(mode="json") for v in validators],
            }
            print(json.dumps(data, indent=2, default=str))
            return

        # Table format
        doc_types = await doc_types_cat.find_all_active()
        if doc_types:
            table = Table(
                title="[brand]Document Types[/brand]",
                border_style="dim",
                show_lines=False,
            )
            table.add_column("Code", style="bold")
            table.add_column("Name")
            table.add_column("Nature")
            table.add_column("Default Fields")
            table.add_column("Validators", justify="right")

            for dt in doc_types:
                table.add_row(
                    dt.code,
                    dt.name,
                    dt.nature.value,
                    ", ".join(dt.default_field_codes) or "—",
                    str(len(dt.validator_ids)),
                )
            console.print(table)

        fields, _ = await fields_cat.find_all()
        if fields:
            table = Table(
                title="\n[brand]Fields[/brand]",
                border_style="dim",
                show_lines=False,
            )
            table.add_column("Code", style="bold")
            table.add_column("Display Name")
            table.add_column("Type")
            table.add_column("Required", justify="center")
            table.add_column("Rules", justify="right")

            for f in fields:
                table.add_row(
                    f.code,
                    f.display_name,
                    f.field_type.value,
                    "✓" if f.required else "",
                    str(len(f.validation_rules)),
                )
            console.print(table)

        validators, _ = await validators_cat.find_all()
        if validators:
            table = Table(
                title="\n[brand]Validators[/brand]",
                border_style="dim",
                show_lines=False,
            )
            table.add_column("Code", style="bold")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Severity")

            for v in validators:
                table.add_row(
                    v.code,
                    v.name,
                    v.validator_type.value,
                    v.severity.value,
                )
            console.print(table)
