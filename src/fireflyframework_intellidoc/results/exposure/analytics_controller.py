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

"""REST controller for processing analytics.

Provides endpoints for aggregated statistics, cost analysis,
and breakdowns by document type, nature, and validation failures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from pyfly.container.stereotypes import rest_controller
from pyfly.web.mappings import get_mapping, request_mapping
from pyfly.web.params import QueryParam

from fireflyframework_intellidoc.results.exposure.schemas import (
    AnalyticsSummaryResponse,
)
from fireflyframework_intellidoc.results.service import ResultService
from fireflyframework_intellidoc.types import DocumentNature


# ── Response DTOs ─────────────────────────────────────────────────────


class DocumentTypeAnalytics(BaseModel):
    """Analytics for a single document type."""

    document_type_code: str
    document_type_name: str
    total_processed: int
    success_rate: float
    average_confidence: float
    average_processing_time_ms: int
    top_validation_failures: list[str] = Field(default_factory=list)


class NatureAnalytics(BaseModel):
    """Analytics for a document nature."""

    nature: DocumentNature
    total_processed: int
    document_type_count: int
    success_rate: float


class ValidationFailureAnalytics(BaseModel):
    """Top validation failure statistics."""

    validator_code: str
    validator_name: str
    failure_count: int
    affected_document_types: list[str]
    most_common_reason: str


class CostPeriod(BaseModel):
    """Cost breakdown for a time period."""

    period: str
    cost_usd: float
    tokens: int
    jobs_count: int


class CostAnalyticsResponse(BaseModel):
    """Cost analysis response."""

    total_cost_usd: float
    total_tokens: int
    breakdown: list[CostPeriod] = Field(default_factory=list)


# ── Controller ────────────────────────────────────────────────────────


@rest_controller
@request_mapping("/api/v1/intellidoc/analytics")
class AnalyticsController:
    """Analytics and statistics for document processing."""

    def __init__(self, result_service: ResultService) -> None:
        self._results = result_service

    @get_mapping("/summary")
    async def get_summary(
        self,
        from_date: QueryParam[datetime | None] = None,
        to_date: QueryParam[datetime | None] = None,
    ) -> AnalyticsSummaryResponse:
        """Get aggregated processing statistics for the given period."""
        data = await self._results.get_analytics(from_date, to_date)
        return AnalyticsSummaryResponse(
            period_start=from_date,
            period_end=to_date,
            **data,
        )

    @get_mapping("/by-document-type")
    async def by_document_type(
        self,
        from_date: QueryParam[datetime | None] = None,
        to_date: QueryParam[datetime | None] = None,
    ) -> list[DocumentTypeAnalytics]:
        """Get analytics broken down by document type."""
        data = await self._results.get_analytics(from_date, to_date)
        return [
            DocumentTypeAnalytics(**dt)
            for dt in data.get("by_document_type", [])
        ]

    @get_mapping("/by-nature")
    async def by_nature(
        self,
        from_date: QueryParam[datetime | None] = None,
        to_date: QueryParam[datetime | None] = None,
    ) -> list[NatureAnalytics]:
        """Get analytics broken down by document nature."""
        data = await self._results.get_analytics(from_date, to_date)
        return [
            NatureAnalytics(**n)
            for n in data.get("by_nature", [])
        ]

    @get_mapping("/validation-failures")
    async def top_validation_failures(
        self,
        limit: QueryParam[int] = 10,
        from_date: QueryParam[datetime | None] = None,
        to_date: QueryParam[datetime | None] = None,
    ) -> list[ValidationFailureAnalytics]:
        """Get the most common validation failures."""
        data = await self._results.get_analytics(from_date, to_date)
        failures = data.get("top_validation_failures", [])
        return [
            ValidationFailureAnalytics(**f)
            for f in failures[:limit]
        ]

    @get_mapping("/cost")
    async def cost_analysis(
        self,
        from_date: QueryParam[datetime | None] = None,
        to_date: QueryParam[datetime | None] = None,
        group_by: QueryParam[str] = "day",
    ) -> CostAnalyticsResponse:
        """Get cost analysis broken down by time period."""
        data = await self._results.get_analytics(from_date, to_date)
        return CostAnalyticsResponse(
            total_cost_usd=data.get("total_cost_usd", 0.0),
            total_tokens=data.get("total_tokens_used", 0),
            breakdown=[
                CostPeriod(**p)
                for p in data.get("cost_breakdown", [])
            ],
        )
