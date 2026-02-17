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

"""Processing job domain model.

A :class:`ProcessingJob` tracks the lifecycle of a single file
submission through the IDP pipeline, from ingestion through
to completion or failure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from fireflyframework_intellidoc.types import JobStatus


class ProcessingJob(BaseModel):
    """Tracks the processing of a file submission."""

    id: UUID = Field(default_factory=uuid4)

    # Source info
    source_type: str
    source_reference: str
    original_filename: str
    file_size_bytes: int = 0
    mime_type: str = ""

    # Processing state
    status: JobStatus = JobStatus.PENDING
    current_step: str = ""
    progress_percent: float = 0.0

    # Results
    total_pages: int = 0
    total_documents_detected: int = 0
    documents_processed: int = 0
    documents_succeeded: int = 0
    documents_failed: int = 0

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    processing_duration_ms: int = 0

    # Cost tracking
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0

    # Error info
    error_message: str | None = None
    error_details: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    tenant_id: str | None = None
    correlation_id: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
