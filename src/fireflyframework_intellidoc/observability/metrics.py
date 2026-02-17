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

"""IDP-specific metric definitions.

Provides pre-defined metric names and a helper for recording
processing statistics. Integrates with pyfly's observability
layer when available.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── Metric Names ──────────────────────────────────────────────────────

JOBS_TOTAL = "intellidoc_jobs_total"
JOBS_DURATION_MS = "intellidoc_jobs_duration_milliseconds"
JOBS_ACTIVE = "intellidoc_jobs_active"

DOCUMENTS_PROCESSED_TOTAL = "intellidoc_documents_processed_total"
DOCUMENTS_CLASSIFIED_TOTAL = "intellidoc_documents_classified_total"
DOCUMENTS_EXTRACTED_TOTAL = "intellidoc_documents_extracted_total"
DOCUMENTS_VALIDATED_TOTAL = "intellidoc_documents_validated_total"

PAGES_PROCESSED_TOTAL = "intellidoc_pages_processed_total"
FIELDS_EXTRACTED_TOTAL = "intellidoc_fields_extracted_total"

VALIDATION_PASS_TOTAL = "intellidoc_validations_passed_total"
VALIDATION_FAIL_TOTAL = "intellidoc_validations_failed_total"

TOKENS_USED_TOTAL = "intellidoc_tokens_used_total"
COST_USD_TOTAL = "intellidoc_cost_usd_total"

INGESTION_DURATION_MS = "intellidoc_ingestion_duration_milliseconds"
PREPROCESSING_DURATION_MS = "intellidoc_preprocessing_duration_milliseconds"
SPLITTING_DURATION_MS = "intellidoc_splitting_duration_milliseconds"
CLASSIFICATION_DURATION_MS = "intellidoc_classification_duration_milliseconds"
EXTRACTION_DURATION_MS = "intellidoc_extraction_duration_milliseconds"
VALIDATION_DURATION_MS = "intellidoc_validation_duration_milliseconds"

ERRORS_TOTAL = "intellidoc_errors_total"


@dataclass
class MetricsCollector:
    """Collects IDP processing metrics in-memory.

    When pyfly's observability module is available, these metrics
    are bridged to Prometheus. Otherwise they serve as internal
    counters for analytics and debugging.
    """

    _counters: dict[str, float] = field(default_factory=dict)
    _gauges: dict[str, float] = field(default_factory=dict)

    def increment(
        self, metric: str, value: float = 1.0, **labels: str
    ) -> None:
        key = self._key(metric, labels)
        self._counters[key] = self._counters.get(key, 0.0) + value

    def set_gauge(
        self, metric: str, value: float, **labels: str
    ) -> None:
        key = self._key(metric, labels)
        self._gauges[key] = value

    def get(self, metric: str, **labels: str) -> float:
        key = self._key(metric, labels)
        return self._counters.get(key, 0.0) + self._gauges.get(key, 0.0)

    @contextmanager
    def timer(self, metric: str, **labels: str):
        """Context manager that records duration in milliseconds."""
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            self.increment(metric, elapsed_ms, **labels)

    def record_job_completed(
        self,
        *,
        status: str,
        duration_ms: int,
        documents: int,
        pages: int,
        tokens: int,
        cost_usd: float,
    ) -> None:
        """Record metrics for a completed job."""
        self.increment(JOBS_TOTAL, status=status)
        self.increment(JOBS_DURATION_MS, duration_ms)
        self.increment(DOCUMENTS_PROCESSED_TOTAL, documents)
        self.increment(PAGES_PROCESSED_TOTAL, pages)
        self.increment(TOKENS_USED_TOTAL, tokens)
        self.increment(COST_USD_TOTAL, cost_usd)

    def record_error(self, error_type: str, stage: str) -> None:
        """Record a processing error."""
        self.increment(ERRORS_TOTAL, error_type=error_type, stage=stage)

    def snapshot(self) -> dict[str, float]:
        """Return a copy of all current metric values."""
        result = {}
        result.update(self._counters)
        result.update(self._gauges)
        return result

    @staticmethod
    def _key(metric: str, labels: dict[str, str]) -> str:
        if not labels:
            return metric
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric}{{{label_str}}}"
