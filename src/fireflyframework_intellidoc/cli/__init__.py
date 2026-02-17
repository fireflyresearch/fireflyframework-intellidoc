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

    app = PyFlyApplication(IntelliDocCLIApp)
    await app.startup()

    runner = app.context.resolve(ShellRunnerPort)
    exit_code = runner.run_cli(sys.argv[1:])

    await app.shutdown()
    return exit_code


def main() -> None:
    """Entry point for the ``intellidoc`` console script."""
    code = asyncio.run(_boot_and_run())
    sys.exit(code)
