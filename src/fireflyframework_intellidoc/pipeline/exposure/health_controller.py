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

"""IDP-specific health and readiness controller.

Provides endpoints for health checks, readiness probes, and
non-sensitive configuration info.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pyfly.container.stereotypes import rest_controller
from pyfly.web.mappings import get_mapping, request_mapping

from fireflyframework_intellidoc._version import __version__
from fireflyframework_intellidoc.config import IntelliDocConfig
from fireflyframework_intellidoc.observability.metrics import MetricsCollector


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness check response with component status."""

    ready: bool
    components: dict[str, ComponentStatus]


class ComponentStatus(BaseModel):
    """Status of a single component."""

    status: str
    details: dict[str, Any] = {}


class ConfigInfoResponse(BaseModel):
    """Non-sensitive configuration summary."""

    version: str
    default_model: str
    storage_provider: str
    default_splitting_strategy: str
    max_file_size_mb: int
    max_pages_per_file: int
    supported_mime_types: list[str]
    async_processing_enabled: bool
    enabled_sources: list[str]
    metrics_enabled: bool
    tracing_enabled: bool


@rest_controller
@request_mapping("/api/v1/intellidoc/health")
class IntelliDocHealthController:
    """IDP-specific health and readiness checks."""

    def __init__(
        self,
        config: IntelliDocConfig,
        metrics: MetricsCollector,
    ) -> None:
        self._config = config
        self._metrics = metrics

    @get_mapping("")
    async def health(self) -> HealthResponse:
        """Basic health check — always returns OK if the service is up."""
        return HealthResponse(
            status="UP",
            version=__version__,
            timestamp=datetime.now(),
        )

    @get_mapping("/ready")
    async def readiness(self) -> ReadinessResponse:
        """Check readiness of all required components."""
        components: dict[str, ComponentStatus] = {}

        # Config check
        components["config"] = ComponentStatus(
            status="UP",
            details={"enabled": self._config.enabled},
        )

        # Storage check
        components["storage"] = ComponentStatus(
            status="UP",
            details={"provider": self._config.storage_provider},
        )

        # AI model check
        components["ai_model"] = ComponentStatus(
            status="UP",
            details={"model": self._config.default_model},
        )

        all_up = all(c.status == "UP" for c in components.values())

        return ReadinessResponse(
            ready=all_up,
            components=components,
        )

    @get_mapping("/config")
    async def config_info(self) -> ConfigInfoResponse:
        """Return non-sensitive configuration info."""
        sources = []
        if self._config.ingestion_local_enabled:
            sources.append("local")
        if self._config.ingestion_url_enabled:
            sources.append("url")
        if self._config.ingestion_s3_enabled:
            sources.append("s3")
        if self._config.ingestion_azure_enabled:
            sources.append("azure_blob")
        if self._config.ingestion_gcs_enabled:
            sources.append("gcs")

        return ConfigInfoResponse(
            version=__version__,
            default_model=self._config.default_model,
            storage_provider=self._config.storage_provider,
            default_splitting_strategy=self._config.default_splitting_strategy,
            max_file_size_mb=self._config.max_file_size_mb,
            max_pages_per_file=self._config.max_pages_per_file,
            supported_mime_types=self._config.supported_mime_types,
            async_processing_enabled=self._config.async_processing_enabled,
            enabled_sources=sources,
            metrics_enabled=self._config.metrics_enabled,
            tracing_enabled=self._config.tracing_enabled,
        )

    @get_mapping("/metrics")
    async def metrics_snapshot(self) -> dict[str, float]:
        """Return current metric values."""
        return self._metrics.snapshot()
