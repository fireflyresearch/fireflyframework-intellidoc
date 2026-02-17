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

"""Rich progress bar for pipeline stage tracking."""

from __future__ import annotations

import sys

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from fireflyframework_intellidoc.cli.banner import console

# Pipeline stages in order, mapped to human-readable labels
STAGE_LABELS: dict[str, str] = {
    "ingesting": "Ingesting",
    "preprocessing": "Preprocessing",
    "splitting": "Splitting",
    "classifying": "Classifying",
    "extracting": "Extracting",
    "validating": "Validating",
    "completed": "Done",
    "failed": "Failed",
    "partially_completed": "Partially completed",
}


class CLIProgress:
    """Manages a Rich progress bar for the processing pipeline.

    Writes to stderr so stdout stays clean for result output.
    Automatically disabled when stdout is not a TTY (piped).
    """

    def __init__(self, filename: str, *, quiet: bool = False) -> None:
        self._filename = filename
        self._quiet = quiet
        self._enabled = not quiet and sys.stderr.isatty()
        self._progress: Progress | None = None
        self._task_id: int | None = None

    def start(self) -> None:
        if not self._enabled:
            return
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[brand]{task.description}[/brand]"),
            BarColumn(bar_width=40),
            TextColumn("[dim]{task.percentage:>3.0f}%[/dim]"),
            TextColumn("[dim]{task.fields[stage]}[/dim]"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            f"Processing {self._filename}",
            total=100,
            stage="Starting...",
        )

    def update(self, status: str, progress_percent: float) -> None:
        if not self._enabled or self._progress is None or self._task_id is None:
            return
        label = STAGE_LABELS.get(status, status.replace("_", " ").title())
        self._progress.update(
            self._task_id,
            completed=progress_percent,
            stage=label,
        )

    def finish(self, status: str) -> None:
        if not self._enabled or self._progress is None:
            return
        label = STAGE_LABELS.get(status, status)
        if self._task_id is not None:
            self._progress.update(self._task_id, completed=100, stage=label)
        self._progress.stop()

        if status == "completed":
            console.print(f"  [success]✓[/success] {self._filename} processed")
        elif status == "failed":
            console.print(f"  [error]✗[/error] {self._filename} failed")
        else:
            console.print(f"  [warning]![/warning] {self._filename} {label.lower()}")
