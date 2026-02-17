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

"""Shell component commands for the IntelliDoc CLI.

Defines ``process`` and ``batch`` commands as ``@shell_component`` beans
with full dependency injection from the pyfly container.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from pyfly.container.stereotypes import shell_component
from pyfly.shell.decorators import shell_method, shell_option

from fireflyframework_intellidoc.cli.banner import console
from fireflyframework_intellidoc.cli.output import format_result
from fireflyframework_intellidoc.cli.progress import CLIProgress
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.pipeline.orchestrator import ProcessingOrchestrator
from fireflyframework_intellidoc.results.exposure.schemas import TargetSchema

# Provider → environment variable mapping
_API_KEY_ENV_VARS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
}


def _resolve_api_key(model: str, api_key: str | None) -> str | None:
    """Resolve API key from flag, env var, or .env file."""
    if api_key:
        return api_key

    provider = model.split(":")[0] if ":" in model else model
    env_var = _API_KEY_ENV_VARS.get(provider)
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key

    # Try .env in CWD
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if env_var and k.strip() == env_var:
                    return v.strip()
    return None


def _set_api_key_env(model: str, api_key: str) -> None:
    """Set the API key in the environment for downstream SDK use."""
    provider = model.split(":")[0] if ":" in model else model
    env_var = _API_KEY_ENV_VARS.get(provider)
    if env_var:
        os.environ[env_var] = api_key


@shell_component
class ProcessCommands:
    """Document processing commands."""

    def __init__(
        self,
        orchestrator: ProcessingOrchestrator,
        config: IntelliDocConfig,
    ) -> None:
        self._orchestrator = orchestrator
        self._config = config

    @shell_method(key="process", help="Process a document file")
    @shell_option("model", help="VLM model in provider:model format (e.g. openai:gpt-4o)", default="")
    @shell_option("api-key", help="API key (or set via env var: OPENAI_API_KEY, etc.)", default="")
    @shell_option("fields", help="Target fields to extract (comma-separated codes)", default="")
    @shell_option("expected-type", help="Skip classification — assume this document type code", default="")
    @shell_option("expected-nature", help="Narrow classification to this nature", default="")
    @shell_option("splitting-strategy", help="Splitting strategy: visual or page_based", default="")
    @shell_option("format", help="Output format: json, table, csv", default="json")
    @shell_option("output", help="Write results to file instead of stdout", default="")
    @shell_option("pretty", is_flag=True, help="Pretty-print JSON output")
    @shell_option("quiet", is_flag=True, help="Suppress progress output")
    async def process(
        self,
        file: str,
        model: str = "",
        api_key: str = "",
        fields: str = "",
        expected_type: str = "",
        expected_nature: str = "",
        splitting_strategy: str = "",
        format: str = "json",
        output: str = "",
        pretty: bool = False,
        quiet: bool = False,
    ) -> None:
        """Process a single document file."""
        file_path = Path(file)
        if not file_path.exists():
            console.print(f"  [error]✗[/error] File not found: {file}")
            sys.exit(1)

        # Resolve model
        effective_model = model or self._config.default_model
        self._config.default_model = effective_model

        # Resolve API key
        key = _resolve_api_key(effective_model, api_key or None)
        if key:
            _set_api_key_env(effective_model, key)

        # Build target schema
        target_schema = None
        if fields:
            target_schema = TargetSchema(field_codes=fields.split(","))

        # Progress bar
        progress = CLIProgress(file_path.name, quiet=quiet)
        progress.start()

        try:
            result = await self._orchestrator.process(
                source_type="local",
                source_reference=str(file_path.resolve()),
                filename=file_path.name,
                expected_type=expected_type or None,
                expected_nature=expected_nature or None,
                splitting_strategy=splitting_strategy or None,
                target_schema=target_schema,
            )

            progress.finish(result.job.status.value)

            # Format and output
            result.model_used = effective_model
            formatted = format_result(result, fmt=format, pretty=pretty)

            if output:
                Path(output).write_text(formatted)
                console.print(f"  [success]✓[/success] Results written to {output}")
            else:
                # Write to stdout (not stderr console)
                print(formatted)

        except Exception as exc:
            progress.finish("failed")
            console.print(f"  [error]✗[/error] Processing failed: {exc}")
            sys.exit(1)

    @shell_method(key="batch", help="Process all documents in a directory")
    @shell_option("model", help="VLM model in provider:model format", default="")
    @shell_option("api-key", help="API key", default="")
    @shell_option("fields", help="Target fields (comma-separated codes)", default="")
    @shell_option("expected-type", help="Assume this document type for all files", default="")
    @shell_option("format", help="Output format: json, table, csv", default="json")
    @shell_option("output", help="Output directory for results", default="")
    @shell_option("parallel", help="Max parallel documents", default=4)
    @shell_option("pretty", is_flag=True, help="Pretty-print JSON")
    @shell_option("quiet", is_flag=True, help="Suppress progress output")
    async def batch(
        self,
        directory: str,
        model: str = "",
        api_key: str = "",
        fields: str = "",
        expected_type: str = "",
        format: str = "json",
        output: str = "",
        parallel: int = 4,
        pretty: bool = False,
        quiet: bool = False,
    ) -> None:
        """Process all supported documents in a directory."""
        dir_path = Path(directory)
        if not dir_path.is_dir():
            console.print(f"  [error]✗[/error] Not a directory: {directory}")
            sys.exit(1)

        supported = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
        files = sorted(
            f for f in dir_path.iterdir() if f.suffix.lower() in supported
        )

        if not files:
            console.print(f"  [warning]![/warning] No supported files in {directory}")
            return

        # Resolve model and API key
        effective_model = model or self._config.default_model
        self._config.default_model = effective_model
        key = _resolve_api_key(effective_model, api_key or None)
        if key:
            _set_api_key_env(effective_model, key)

        target_schema = TargetSchema(field_codes=fields.split(",")) if fields else None
        output_dir = Path(output) if output else None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        if not quiet:
            console.print(
                f"  [info]→[/info] Processing {len(files)} files"
                f" with {effective_model}"
            )

        succeeded = 0
        failed = 0

        for file_path in files:
            progress = CLIProgress(file_path.name, quiet=quiet)
            progress.start()

            try:
                result = await self._orchestrator.process(
                    source_type="local",
                    source_reference=str(file_path.resolve()),
                    filename=file_path.name,
                    expected_type=expected_type or None,
                    target_schema=target_schema,
                )
                progress.finish(result.job.status.value)

                result.model_used = effective_model
                formatted = format_result(result, fmt=format, pretty=pretty)

                if output_dir:
                    out_file = output_dir / f"{file_path.stem}.{format}"
                    out_file.write_text(formatted)
                else:
                    print(formatted)

                succeeded += 1

            except Exception as exc:
                progress.finish("failed")
                console.print(f"  [error]✗[/error] {file_path.name}: {exc}")
                failed += 1

        if not quiet:
            console.print(
                f"\n  [info]Batch complete:[/info]"
                f" [success]{succeeded} succeeded[/success],"
                f" [error]{failed} failed[/error]"
            )
