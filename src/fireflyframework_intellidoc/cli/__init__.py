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

"""IntelliDoc CLI — standalone command-line interface.

Entry point for the ``intellidoc`` command, built on pyfly's shell
infrastructure with full DI container access to the processing engine.
"""

from __future__ import annotations

import asyncio
import sys


async def _boot_and_run() -> int:
    from pyfly.core.application import PyFlyApplication
    from pyfly.shell.ports.outbound import ShellRunnerPort

    from fireflyframework_intellidoc.cli.app import IntelliDocCLIApp
    from fireflyframework_intellidoc.cli.shell_adapter import IntelliDocShellAdapter

    app = PyFlyApplication(IntelliDocCLIApp)
    await app.startup()

    # PyFly's shell auto-config may register the default ClickShellAdapter
    # before IntelliDoc's CLI auto-config can provide IntelliDocShellAdapter.
    # The default adapter has all @shell_component commands registered on it
    # by pyfly's shell infrastructure. We create a branded adapter and copy
    # the discovered commands onto it so we get --version + banner + commands.
    base_runner = app.context.get_bean(ShellRunnerPort)
    adapter = IntelliDocShellAdapter()

    # Copy commands discovered by pyfly's shell infrastructure
    if hasattr(base_runner, "_root") and hasattr(base_runner._root, "commands"):
        for name, cmd in base_runner._root.commands.items():
            adapter._root.add_command(cmd, name)

    exit_code = adapter.run_cli(sys.argv[1:])

    await app.shutdown()
    return exit_code


def main() -> None:
    """Entry point for the ``intellidoc`` console script."""
    code = asyncio.run(_boot_and_run())
    sys.exit(code)
