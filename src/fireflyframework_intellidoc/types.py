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

"""Shared types, type aliases, and enumerations for IntelliDoc.

Centralises enums and lightweight value types used across multiple
modules so that domain models and ports remain decoupled.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field


# ── Document Nature ─────────────────────────────────────────────────────


class DocumentNature(StrEnum):
    """Broad nature categories for documents."""

    IDENTITY = "identity"
    FINANCIAL = "financial"
    LEGAL = "legal"
    MEDICAL = "medical"
    GOVERNMENT = "government"
    EDUCATIONAL = "educational"
    COMMERCIAL = "commercial"
    INSURANCE = "insurance"
    REAL_ESTATE = "real_estate"
    HR = "hr"
    CORRESPONDENCE = "correspondence"
    TECHNICAL = "technical"
    OTHER = "other"


# ── Field Types ─────────────────────────────────────────────────────────


class FieldType(StrEnum):
    """Types of extractable fields."""

    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"
    BOOLEAN = "boolean"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    TABLE = "table"
    LIST = "list"
    ENUM = "enum"
    IMAGE_REGION = "image_region"


# ── Validator Types ─────────────────────────────────────────────────────


class ValidatorType(StrEnum):
    """Types of validators."""

    FORMAT = "format"
    RANGE = "range"
    REQUIRED = "required"
    CROSS_FIELD = "cross_field"
    VISUAL = "visual"
    BUSINESS_RULE = "business_rule"
    COMPLETENESS = "completeness"
    CHECKSUM = "checksum"
    LOOKUP = "lookup"


class ValidatorSeverity(StrEnum):
    """Severity level of validation failures."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ── Job Status ──────────────────────────────────────────────────────────


class JobStatus(StrEnum):
    """Status of a processing job."""

    PENDING = "pending"
    INGESTING = "ingesting"
    PREPROCESSING = "preprocessing"
    SPLITTING = "splitting"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    CANCELLED = "cancelled"


# ── Document Confidence ─────────────────────────────────────────────────


class DocumentConfidence(StrEnum):
    """Confidence level of processing results."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"

    @classmethod
    def from_score(cls, score: float) -> DocumentConfidence:
        """Derive confidence level from a numeric score."""
        if score >= 0.9:
            return cls.HIGH
        if score >= 0.7:
            return cls.MEDIUM
        if score >= 0.5:
            return cls.LOW
        return cls.VERY_LOW


# ── Lightweight Value Types ─────────────────────────────────────────────


class PageImage(BaseModel):
    """A preprocessed page image."""

    page_number: int
    image_path: Path
    width: int = 0
    height: int = 0
    dpi: int = 300
    rotation_applied: float = 0.0
    enhancements_applied: list[str] = Field(default_factory=list)
    quality_score: float = 1.0


class FileReference(BaseModel):
    """Normalized reference to a file from any source."""

    source_type: str
    source_reference: str
    filename: str
    mime_type: str
    file_size_bytes: int = 0
    content_path: Path | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentBoundary(BaseModel):
    """Detected boundary between documents in a multi-doc file."""

    start_page: int
    end_page: int
    confidence: float = 1.0
    reasoning: str = ""
    detected_type_hint: str = ""


class PageRange(BaseModel):
    """A range of pages within a file."""

    start: int
    end: int

    @property
    def count(self) -> int:
        return self.end - self.start + 1
