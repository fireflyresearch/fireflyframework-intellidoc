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

"""Exception hierarchy for the IntelliDoc IDP framework.

All exceptions inherit from :class:`IntelliDocException` which itself
extends pyfly's :class:`PyFlyException` for seamless integration with
the framework's error handling and HTTP error mapping.
"""

from __future__ import annotations

from typing import Any


class IntelliDocException(Exception):
    """Base exception for all IntelliDoc errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code.
        context: Additional metadata about the error.
    """

    def __init__(
        self,
        message: str = "",
        *,
        code: str = "INTELLIDOC_ERROR",
        context: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.context = context or {}
        super().__init__(message)


# ── Catalog Errors ──────────────────────────────────────────────────────


class CatalogException(IntelliDocException):
    """Base for catalog-related errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "CATALOG_ERROR"), **kwargs)


class DocumentTypeNotFoundException(CatalogException):
    """Raised when a referenced document type does not exist."""

    def __init__(self, identifier: str, **kwargs: Any) -> None:
        super().__init__(
            f"Document type not found: {identifier}",
            code="DOCUMENT_TYPE_NOT_FOUND",
            context={"identifier": identifier},
            **kwargs,
        )


class DocumentTypeAlreadyExistsException(CatalogException):
    """Raised when trying to create a document type with a duplicate code."""

    def __init__(self, code: str, **kwargs: Any) -> None:
        super().__init__(
            f"Document type already exists with code: {code}",
            code="DOCUMENT_TYPE_DUPLICATE",
            context={"document_type_code": code},
            **kwargs,
        )


class ValidatorNotFoundException(CatalogException):
    """Raised when a referenced validator does not exist."""

    def __init__(self, identifier: str, **kwargs: Any) -> None:
        super().__init__(
            f"Validator not found: {identifier}",
            code="VALIDATOR_NOT_FOUND",
            context={"identifier": identifier},
            **kwargs,
        )


class ValidatorAlreadyExistsException(CatalogException):
    """Raised when trying to create a validator with a duplicate code."""

    def __init__(self, code: str, **kwargs: Any) -> None:
        super().__init__(
            f"Validator already exists with code: {code}",
            code="VALIDATOR_DUPLICATE",
            context={"validator_code": code},
            **kwargs,
        )


class FieldNotFoundException(CatalogException):
    """Raised when a referenced catalog field does not exist."""

    def __init__(self, identifier: str, **kwargs: Any) -> None:
        super().__init__(
            f"Field not found: {identifier}",
            code="FIELD_NOT_FOUND",
            context={"identifier": identifier},
            **kwargs,
        )


class FieldAlreadyExistsException(CatalogException):
    """Raised when trying to create a field with a duplicate code."""

    def __init__(self, code: str, **kwargs: Any) -> None:
        super().__init__(
            f"Field already exists with code: {code}",
            code="FIELD_DUPLICATE",
            context={"field_code": code},
            **kwargs,
        )


class TargetSchemaResolutionException(CatalogException):
    """Raised when target schema field codes cannot be resolved."""

    def __init__(self, missing_codes: list[str], **kwargs: Any) -> None:
        super().__init__(
            f"Could not resolve field codes: {', '.join(missing_codes)}",
            code="TARGET_SCHEMA_RESOLUTION_ERROR",
            context={"missing_codes": missing_codes},
            **kwargs,
        )


# ── Ingestion Errors ────────────────────────────────────────────────────


class IngestionException(IntelliDocException):
    """Base for file ingestion errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "INGESTION_ERROR"), **kwargs)


class FileSourceException(IngestionException):
    """Raised when a file cannot be read from its source."""

    def __init__(self, source_type: str, reference: str, reason: str = "", **kwargs: Any) -> None:
        super().__init__(
            f"Failed to read file from {source_type}: {reference}. {reason}".strip(),
            code="FILE_SOURCE_ERROR",
            context={"source_type": source_type, "reference": reference},
            **kwargs,
        )


class UnsupportedFileTypeException(IngestionException):
    """Raised when the file type is not supported."""

    def __init__(self, mime_type: str, **kwargs: Any) -> None:
        super().__init__(
            f"Unsupported file type: {mime_type}",
            code="UNSUPPORTED_FILE_TYPE",
            context={"mime_type": mime_type},
            **kwargs,
        )


class FileTooLargeException(IngestionException):
    """Raised when the file exceeds the maximum allowed size."""

    def __init__(self, file_size_mb: float, max_size_mb: float, **kwargs: Any) -> None:
        super().__init__(
            f"File size {file_size_mb:.1f}MB exceeds maximum {max_size_mb:.1f}MB",
            code="FILE_TOO_LARGE",
            context={"file_size_mb": file_size_mb, "max_size_mb": max_size_mb},
            **kwargs,
        )


# ── Pre-processing Errors ──────────────────────────────────────────────


class PreProcessingException(IntelliDocException):
    """Base for pre-processing errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "PREPROCESSING_ERROR"), **kwargs)


class PageExtractionException(PreProcessingException):
    """Raised when pages cannot be extracted from a document."""

    def __init__(self, reason: str = "", **kwargs: Any) -> None:
        super().__init__(
            f"Failed to extract pages: {reason}",
            code="PAGE_EXTRACTION_ERROR",
            **kwargs,
        )


class QualityTooLowException(PreProcessingException):
    """Raised when document quality is below the minimum threshold."""

    def __init__(self, quality_score: float, threshold: float, **kwargs: Any) -> None:
        super().__init__(
            f"Document quality {quality_score:.2f} is below threshold {threshold:.2f}",
            code="QUALITY_TOO_LOW",
            context={"quality_score": quality_score, "threshold": threshold},
            **kwargs,
        )


# ── Splitting Errors ────────────────────────────────────────────────────


class SplittingException(IntelliDocException):
    """Base for document splitting errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "SPLITTING_ERROR"), **kwargs)


# ── Classification Errors ──────────────────────────────────────────────


class ClassificationException(IntelliDocException):
    """Base for classification errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "CLASSIFICATION_ERROR"), **kwargs)


class ClassificationConfidenceTooLowException(ClassificationException):
    """Raised when classification confidence is below the threshold."""

    def __init__(self, confidence: float, threshold: float, **kwargs: Any) -> None:
        super().__init__(
            f"Classification confidence {confidence:.2f} is below threshold {threshold:.2f}",
            code="CLASSIFICATION_CONFIDENCE_LOW",
            context={"confidence": confidence, "threshold": threshold},
            **kwargs,
        )


# ── Extraction Errors ──────────────────────────────────────────────────


class ExtractionException(IntelliDocException):
    """Base for data extraction errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "EXTRACTION_ERROR"), **kwargs)


# ── Validation Errors ──────────────────────────────────────────────────


class DocumentValidationException(IntelliDocException):
    """Base for document validation errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "VALIDATION_ERROR"), **kwargs)


# ── Pipeline Errors ────────────────────────────────────────────────────


class PipelineException(IntelliDocException):
    """Base for pipeline orchestration errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "PIPELINE_ERROR"), **kwargs)


class JobNotFoundException(IntelliDocException):
    """Raised when a processing job is not found."""

    def __init__(self, job_id: str, **kwargs: Any) -> None:
        super().__init__(
            f"Processing job not found: {job_id}",
            code="JOB_NOT_FOUND",
            context={"job_id": job_id},
            **kwargs,
        )


# ── Storage Errors ─────────────────────────────────────────────────────


class StorageException(IntelliDocException):
    """Base for document storage errors."""

    def __init__(self, message: str = "", **kwargs: Any) -> None:
        super().__init__(message, code=kwargs.pop("code", "STORAGE_ERROR"), **kwargs)
