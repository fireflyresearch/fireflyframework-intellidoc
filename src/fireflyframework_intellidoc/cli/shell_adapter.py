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

"""IntelliDoc shell adapter — extends pyfly's ClickShellAdapter for CLI use.

Provides a branded Click group with the IntelliDoc banner and
a ``run_cli`` method for proper standalone terminal behavior
(colors, formatted help, exit codes).
"""

from __future__ import annotations

import click
from pyfly.shell.adapters.click_adapter import ClickShellAdapter

from fireflyframework_intellidoc.cli.banner import VERSION, print_banner


def _print_version(ctx: click.Context, _param: click.Parameter, value: bool) -> None:
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"intellidoc {VERSION}")
    ctx.exit()


class IntelliDocGroup(click.Group):
    """Click Group subclass that shows the IntelliDoc banner on --help."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        print_banner()
        super().format_help(ctx, formatter)


class IntelliDocShellAdapter(ClickShellAdapter):
    """Shell adapter with IntelliDoc branding and standalone CLI support.

    Extends :class:`ClickShellAdapter` with:

    - A custom :class:`IntelliDocGroup` root that prints the banner on ``--help``
    - A :meth:`run_cli` method that invokes Click with ``standalone_mode=True``
      for proper terminal behavior (colors, formatted errors, exit codes)
    """

    def __init__(self) -> None:
        super().__init__(
            name="intellidoc",
            help_text=(
                "Intelligent Document Processing powered by Vision-Language Models"
            ),
        )
        # Replace root with branded group
        self._root = IntelliDocGroup(
            name="intellidoc",
            help="Intelligent Document Processing powered by Vision-Language Models",
        )
        # Add --version / -V option
        self._root.params.append(
            click.Option(
                ["--version", "-V"],
                is_flag=True,
                expose_value=False,
                is_eager=True,
                callback=_print_version,
                help="Show version and exit.",
            )
        )

    def run_cli(self, args: list[str] | None = None) -> int:
        """Run as a standalone CLI with proper terminal behavior.

        Uses Click's ``standalone_mode=True`` for formatted help,
        colored output, and proper error handling. Returns exit code.
        """
        try:
            self._root.main(args=args or [], standalone_mode=True)
            return 0
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
