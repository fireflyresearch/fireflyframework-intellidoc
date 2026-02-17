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

"""IntelliDoc CLI application class.

Bootstraps a minimal pyfly application context with shell support
enabled and all IntelliDoc processing beans available via DI.
"""

from __future__ import annotations

from pyfly.core import pyfly_application


@pyfly_application(
    name="intellidoc",
    scan_packages=[
        "fireflyframework_intellidoc",
    ],
)
class IntelliDocCLIApp:
    """Standalone IntelliDoc CLI application.

    Boots the pyfly DI container with all IntelliDoc auto-configurations
    (processing engine, validators, splitters) plus CLI-specific beans
    (in-memory adapters, shell commands).
    """
