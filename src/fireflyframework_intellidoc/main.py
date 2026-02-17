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

"""Ready-to-run ASGI entry point for IntelliDoc.

This module provides a pre-configured ``app`` variable that can be started
directly with ``pyfly run`` — no user-defined application class required.

Usage::

    # In pyfly.yaml
    pyfly:
      app:
        module: fireflyframework_intellidoc.main:app
      intellidoc:
        enabled: true
        default_model: "openai:gpt-4o"

    # Then run:
    pyfly run

    # Or directly:
    pyfly run --app fireflyframework_intellidoc.main:app
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from pyfly.core import PyFlyApplication, pyfly_application
from pyfly.web.adapters.starlette.app import create_app

from fireflyframework_intellidoc._version import __version__


@pyfly_application(
    name="IntelliDoc",
    version=__version__,
    scan_packages=["fireflyframework_intellidoc"],
    description="Intelligent Document Processing powered by VLMs",
)
class _IntelliDocApplication:
    """Built-in application class — users don't need to create their own."""


_pyfly = PyFlyApplication(_IntelliDocApplication)


@asynccontextmanager
async def _lifespan(asgi_app):
    """Manage IntelliDoc startup and shutdown lifecycle."""
    _pyfly._route_metadata = getattr(asgi_app.state, "pyfly_route_metadata", [])
    _pyfly._docs_enabled = getattr(asgi_app.state, "pyfly_docs_enabled", False)
    _pyfly._host = str(_pyfly.config.get("pyfly.web.host", "0.0.0.0"))
    _pyfly._port = int(_pyfly.config.get("pyfly.web.port", 8080))
    await _pyfly.startup()
    yield
    await _pyfly.shutdown()


app = create_app(
    title="IntelliDoc",
    version=__version__,
    description="Catalog-driven Intelligent Document Processing API",
    context=_pyfly.context,
    lifespan=_lifespan,
    docs_enabled=True,
    actuator_enabled=True,
)
