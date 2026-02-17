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

"""REST controller for processing result retrieval.

Provides endpoints to retrieve complete results, individual
document details, extracted data, and analytics summaries.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from pyfly.container.stereotypes import rest_controller
from pyfly.web.mappings import get_mapping, request_mapping
from pyfly.web.params import PathVar, QueryParam

from fireflyframework_intellidoc.results.exposure.schemas import (
    AnalyticsSummaryResponse,
    DocumentResultResponse,
    ProcessingResultResponse,
)
from fireflyframework_intellidoc.results.service import ResultService


@rest_controller
@request_mapping("/api/v1/intellidoc/results")
class ResultController:
    """Retrieve processing results and analytics."""

    def __init__(self, result_service: ResultService) -> None:
        self._results = result_service

    @get_mapping("/{job_id}")
    async def get_result(
        self, job_id: PathVar[UUID]
    ) -> ProcessingResultResponse:
        """Get the complete processing result for a job."""
        result = await self._results.get_processing_result(job_id)
        return ProcessingResultResponse.from_domain(result)

    @get_mapping("/{job_id}/documents/{document_id}")
    async def get_document_result(
        self,
        job_id: PathVar[UUID],
        document_id: PathVar[UUID],
    ) -> DocumentResultResponse:
        """Get result details for a specific document within a job."""
        doc = await self._results.get_document_result(job_id, document_id)
        return DocumentResultResponse.from_domain(doc)

    @get_mapping("/{job_id}/extracted-data")
    async def get_extracted_data(
        self, job_id: PathVar[UUID]
    ) -> list[ExtractedDataResponse]:
        """Get only the extracted fields for all documents in a job.

        Useful for downstream integrations that only need the data,
        not the full classification/validation details.
        """
        result = await self._results.get_processing_result(job_id)
        return [
            ExtractedDataResponse(
                document_id=doc.id,
                document_type_code=doc.document_type_code,
                page_range=f"{doc.page_range_start}-{doc.page_range_end}",
                fields=doc.extracted_fields,
                confidence=doc.extraction_confidence,
                is_valid=doc.is_valid,
            )
            for doc in result.documents
        ]

    @get_mapping("/{job_id}/export")
    async def export_result(
        self,
        job_id: PathVar[UUID],
        format: QueryParam[str] = "json",
    ) -> ExportResponse:
        """Export results in JSON or CSV format.

        Supported formats: ``json``, ``csv``.
        """
        result = await self._results.get_processing_result(job_id)

        if format == "csv":
            content = self._to_csv(result)
            return ExportResponse(
                format="csv",
                content=content,
                filename=f"result_{job_id}.csv",
            )

        content = ProcessingResultResponse.from_domain(result).model_dump_json(
            indent=2
        )
        return ExportResponse(
            format="json",
            content=content,
            filename=f"result_{job_id}.json",
        )

    @get_mapping("/analytics")
    async def get_analytics(
        self,
        from_date: QueryParam[datetime | None] = None,
        to_date: QueryParam[datetime | None] = None,
    ) -> AnalyticsSummaryResponse:
        """Get aggregated analytics for the given period."""
        data = await self._results.get_analytics(from_date, to_date)
        return AnalyticsSummaryResponse(**data)

    def _to_csv(self, result: Any) -> str:
        """Convert processing result documents to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "document_id",
            "document_type",
            "pages",
            "classification_confidence",
            "is_valid",
            "validation_score",
            "overall_confidence",
            "fields_json",
        ])

        for doc in result.documents:
            writer.writerow([
                str(doc.id),
                doc.document_type_code or "unknown",
                f"{doc.page_range_start}-{doc.page_range_end}",
                f"{doc.classification_confidence:.3f}",
                doc.is_valid,
                f"{doc.validation_score:.3f}",
                doc.overall_confidence.value,
                json.dumps(doc.extracted_fields),
            ])

        return output.getvalue()


# ── Helper DTOs ───────────────────────────────────────────────────────


class ExtractedDataResponse(BaseModel):
    """Minimal response with just extracted fields."""

    document_id: UUID
    document_type_code: str | None
    page_range: str
    fields: dict[str, Any]
    confidence: dict[str, float]
    is_valid: bool


class ExportResponse(BaseModel):
    """Exported result content."""

    format: str
    content: str
    filename: str
