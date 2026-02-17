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

"""Configuration properties for the IntelliDoc IDP framework.

Uses pyfly's ``@config_properties`` for typed binding from YAML config
and environment variables with the ``pyfly.intellidoc.*`` prefix.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pyfly.core.config import config_properties


@config_properties(prefix="pyfly.intellidoc")
@dataclass
class IntelliDocConfig:
    """Configuration properties bound from ``pyfly.intellidoc.*``.

    All properties can be overridden via environment variables using the
    pattern ``PYFLY_INTELLIDOC_<PROPERTY_NAME>`` (uppercased, dots replaced
    with underscores).
    """

    # ── General ──────────────────────────────────────────────────────
    enabled: bool = True
    api_prefix: str = "/api/v1/intellidoc"

    # ── AI Models ────────────────────────────────────────────────────
    default_model: str = "openai:gpt-4o"
    classification_model: str = ""
    extraction_model: str = ""
    splitting_model: str = ""
    validation_model: str = ""
    default_temperature: float = 0.1

    # ── Processing Pipeline ──────────────────────────────────────────
    max_pages_per_file: int = 500
    max_file_size_mb: int = 100
    default_splitting_strategy: str = "visual"
    default_dpi: int = 300
    parallel_documents: int = 5

    # ── Timeouts (seconds) ───────────────────────────────────────────
    ingestion_timeout: int = 60
    preprocessing_timeout: int = 120
    splitting_timeout: int = 60
    classification_timeout: int = 30
    extraction_timeout: int = 60
    validation_timeout: int = 30

    # ── Retries ──────────────────────────────────────────────────────
    ingestion_retries: int = 2
    splitting_retries: int = 1
    classification_retries: int = 2
    extraction_retries: int = 2

    # ── Pre-processing ───────────────────────────────────────────────
    auto_rotate: bool = True
    auto_enhance: bool = True
    auto_denoise: bool = True
    quality_threshold: float = 0.3

    # ── Classification ───────────────────────────────────────────────
    default_confidence_threshold: float = 0.7
    max_classification_candidates: int = 5

    # ── Extraction ───────────────────────────────────────────────────
    extraction_strategy: str = "single_pass"
    max_extraction_retries: int = 2

    # ── Storage ──────────────────────────────────────────────────────
    storage_provider: str = "local"
    storage_local_path: str = "/var/intellidoc/storage"
    storage_bucket: str = ""
    storage_container: str = ""
    storage_prefix: str = "intellidoc/"
    store_original_files: bool = True
    store_page_images: bool = True
    store_enhanced_images: bool = False

    # ── Ingestion Sources ────────────────────────────────────────────
    ingestion_local_enabled: bool = True
    ingestion_url_enabled: bool = True
    ingestion_s3_enabled: bool = False
    ingestion_azure_enabled: bool = False
    ingestion_gcs_enabled: bool = False

    # ── S3 Configuration ─────────────────────────────────────────────
    s3_region: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_endpoint_url: str = ""

    # ── Azure Configuration ──────────────────────────────────────────
    azure_connection_string: str = ""
    azure_account_url: str = ""

    # ── GCS Configuration ────────────────────────────────────────────
    gcs_project_id: str = ""
    gcs_credentials_path: str = ""

    # ── Temp Files ───────────────────────────────────────────────────
    temp_dir: str = "/tmp/intellidoc"
    cleanup_temp_after_processing: bool = True

    # ── Observability ────────────────────────────────────────────────
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    cost_tracking_enabled: bool = True

    # ── Async Processing ─────────────────────────────────────────────
    async_processing_enabled: bool = True
    job_expiry_hours: int = 168

    # ── Supported MIME Types ─────────────────────────────────────────
    supported_mime_types: list[str] = field(
        default_factory=lambda: [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/tiff",
            "image/bmp",
            "image/webp",
            "image/gif",
        ]
    )

    def get_model(self, stage: str) -> str:
        """Return the model for a processing stage, falling back to default."""
        stage_model = getattr(self, f"{stage}_model", "")
        return stage_model if stage_model else self.default_model
