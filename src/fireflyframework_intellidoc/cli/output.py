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

"""Output formatters for CLI results — JSON, table, and CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from rich.table import Table

from fireflyframework_intellidoc.cli.banner import console
from fireflyframework_intellidoc.results.domain.processing_result import (
    DocumentResult,
    ProcessingResult,
)


def format_result(
    result: ProcessingResult,
    fmt: str = "json",
    pretty: bool = False,
) -> str:
    """Format a ProcessingResult for CLI output.

    Returns a string suitable for stdout.
    """
    if fmt == "table":
        return _format_table(result)
    if fmt == "csv":
        return _format_csv(result)
    return _format_json(result, pretty=pretty)


def _format_json(result: ProcessingResult, *, pretty: bool = False) -> str:
    data = _result_to_dict(result)
    if pretty:
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)
    return json.dumps(data, default=str, ensure_ascii=False)


def _format_table(result: ProcessingResult) -> str:
    """Render a Rich table to a string and return it."""
    buf = io.StringIO()
    table_console = console.__class__(file=buf, force_terminal=False, width=120)

    for i, doc in enumerate(result.documents):
        doc_type = doc.document_type_code or "unknown"
        confidence = f"{doc.classification_confidence:.0%}"

        table_console.print(
            f"\n  [brand]Document {i + 1}/{len(result.documents)}[/brand]"
            f" — {doc_type} ({confidence} confidence)"
        )

        table = Table(border_style="dim", show_lines=False, pad_edge=True)
        table.add_column("Field", style="bold", min_width=20)
        table.add_column("Value", min_width=30)
        table.add_column("Confidence", justify="right", min_width=12)

        for field_code, value in doc.extracted_fields.items():
            conf = doc.extraction_confidence.get(field_code, 0.0)
            conf_str = f"{conf:.0%}" if conf else "—"
            table.add_row(field_code, str(value), conf_str)

        table_console.print(table)

        # Validation summary
        passed = sum(1 for v in doc.validation_results if v.passed)
        failed = sum(1 for v in doc.validation_results if not v.passed)
        warnings = sum(
            1 for v in doc.validation_results if not v.passed and v.severity.value == "warning"
        )
        table_console.print(
            f"  Validation: [success]{passed} passed[/success]"
            f", [error]{failed} failed[/error]"
            f", [warning]{warnings} warnings[/warning]"
        )

    # Summary line
    job = result.job
    table_console.print(
        f"\n  [dim]Processed in {job.processing_duration_ms}ms"
        f" | {job.total_tokens_used} tokens"
        f" | ${job.total_cost_usd:.4f}[/dim]\n"
    )

    return buf.getvalue()


def _format_csv(result: ProcessingResult) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["document_index", "document_type", "field", "value", "confidence"])

    for i, doc in enumerate(result.documents):
        for field_code, value in doc.extracted_fields.items():
            conf = doc.extraction_confidence.get(field_code, 0.0)
            writer.writerow([
                i + 1,
                doc.document_type_code or "unknown",
                field_code,
                str(value),
                f"{conf:.4f}",
            ])

    return buf.getvalue()


def _result_to_dict(result: ProcessingResult) -> dict[str, Any]:
    """Convert ProcessingResult to a CLI-friendly dict (simplified)."""
    return {
        "status": result.job.status.value,
        "processing_time_ms": result.job.processing_duration_ms,
        "model": result.model_used,
        "total_pages": result.job.total_pages,
        "total_documents": len(result.documents),
        "tokens_used": result.job.total_tokens_used,
        "cost_usd": result.job.total_cost_usd,
        "documents": [_doc_to_dict(d) for d in result.documents],
    }


def _doc_to_dict(doc: DocumentResult) -> dict[str, Any]:
    return {
        "document_type": doc.document_type_code,
        "confidence": doc.classification_confidence,
        "fields": {
            code: {
                "value": value,
                "confidence": doc.extraction_confidence.get(code, 0.0),
            }
            for code, value in doc.extracted_fields.items()
        },
        "validation": {
            "is_valid": doc.is_valid,
            "passed": sum(1 for v in doc.validation_results if v.passed),
            "failed": sum(1 for v in doc.validation_results if not v.passed),
        },
        "pages": {"start": doc.page_range_start, "end": doc.page_range_end},
    }
