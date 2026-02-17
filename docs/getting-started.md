# Getting Started

**fireflyframework-intellidoc — Step-by-Step Tutorial**

> Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0

---

This guide walks you through setting up an IDP service from scratch, creating
your first document type, processing documents, and retrieving results.

## Prerequisites

- Python >= 3.13
- A VLM-capable API key (e.g., OpenAI GPT-4o, Anthropic Claude)
- (Optional) PostgreSQL for persistent storage
- (Optional) Poppler for PDF→image conversion

## Step 1: Install

```bash
# Create a new project
mkdir my-idp-service && cd my-idp-service
python -m venv .venv && source .venv/bin/activate

# Install with web server and PDF support
pip install "fireflyframework-intellidoc[web,pdf-images]"
```

## Step 2: Configure

Create `pyfly.yaml`:

```yaml
pyfly:
  # Point to IntelliDoc's built-in application
  app:
    module: fireflyframework_intellidoc.main:app

  # Web server
  web:
    port: 8080

  # IntelliDoc configuration
  intellidoc:
    enabled: true

    # AI Model — set your preferred VLM
    default_model: "openai:gpt-4o"

    # Storage — local filesystem for development
    storage_provider: "local"
    storage_local_path: "./intellidoc-storage"

    # Ingestion sources
    ingestion_local_enabled: true
    ingestion_url_enabled: true

    # Processing
    default_splitting_strategy: "page_based"  # or "visual" for multi-doc files
    default_confidence_threshold: 0.7
    max_file_size_mb: 50

    # Pre-processing
    auto_rotate: true
    auto_enhance: true
    quality_threshold: 0.3

    # Async processing
    async_processing_enabled: true
```

Set your API key:
```bash
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Step 3: Start the Service

```bash
pyfly run
```

That's it — no application class needed. IntelliDoc ships with a built-in `main.py`
that wires up all controllers, services, and auto-configurations automatically.

You can also start it directly:
```bash
pyfly run --app fireflyframework_intellidoc.main:app
```

<details>
<summary><strong>Advanced: Custom application class</strong></summary>

If you need to add your own controllers, services, or custom beans alongside IntelliDoc,
create a custom application class:

```python
# src/my_idp_service/app.py
from pyfly.core import pyfly_application


@pyfly_application(
    name="my-idp-service",
    scan_packages=[
        "my_idp_service",              # Your own beans
        "fireflyframework_intellidoc",  # IntelliDoc beans
    ],
)
class MyIDPApp:
    pass
```

```python
# src/my_idp_service/main.py
from contextlib import asynccontextmanager

from pyfly.core import PyFlyApplication
from pyfly.web.adapters.starlette.app import create_app

from my_idp_service.app import MyIDPApp

_pyfly = PyFlyApplication(MyIDPApp)


@asynccontextmanager
async def _lifespan(app):
    _pyfly._route_metadata = getattr(app.state, "pyfly_route_metadata", [])
    _pyfly._docs_enabled = getattr(app.state, "pyfly_docs_enabled", False)
    _pyfly._host = str(_pyfly.config.get("pyfly.web.host", "0.0.0.0"))
    _pyfly._port = int(_pyfly.config.get("pyfly.web.port", 8080))
    await _pyfly.startup()
    yield
    await _pyfly.shutdown()


app = create_app(
    title="My IDP Service",
    version="0.1.0",
    context=_pyfly.context,
    lifespan=_lifespan,
)
```

Update `pyfly.yaml`:
```yaml
pyfly:
  app:
    module: my_idp_service.main:app
```
</details>

The service starts on `http://localhost:8080`. Verify with:

```bash
curl http://localhost:8080/api/v1/intellidoc/health
```

Expected response:
```json
{
  "status": "UP",
  "version": "26.02.01",
  "timestamp": "2026-02-17T10:00:00"
}
```

## Step 5: Create Your First Document Type

Let's set up an invoice processing pipeline.

### 5.1 Create the Document Type

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice",
    "name": "Commercial Invoice",
    "description": "A commercial invoice for goods or services rendered, containing line items and payment details",
    "nature": "financial",
    "visual_description": "A formal document with a company logo at the top, an invoice number, billing and shipping addresses, a table of line items with descriptions, quantities, and prices, subtotals, tax, and a total amount due",
    "visual_cues": [
      "company logo or letterhead",
      "invoice number prominently displayed",
      "table with line items",
      "subtotal, tax, and total amount",
      "billing address and shipping address",
      "payment terms or due date"
    ],
    "sample_keywords": [
      "invoice", "bill to", "ship to", "total", "subtotal",
      "tax", "due date", "payment terms", "PO number", "quantity"
    ],
    "classification_confidence_threshold": 0.75,
    "supported_languages": ["en", "fr", "de", "es"]
  }'
```

Save the returned `id` — you'll need it for the next steps.

### 5.2 Create Catalog Fields

Create reusable field definitions in the fields catalog:

```bash
# Core invoice fields
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_number",
    "display_name": "Invoice Number",
    "field_type": "text",
    "description": "The unique invoice identifier",
    "required": true,
    "location_hint": "Usually near the top of the document",
    "validation_rules": [
      {"rule_type": "required", "severity": "error", "message": "Invoice number is required"}
    ]
  }'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_date",
    "display_name": "Invoice Date",
    "field_type": "date",
    "description": "The date the invoice was issued",
    "required": true,
    "format_pattern": "YYYY-MM-DD",
    "validation_rules": [
      {"rule_type": "format", "config": {"format": "date"}, "message": "Must be a valid date"}
    ]
  }'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "due_date", "display_name": "Due Date", "field_type": "date"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "vendor_name", "display_name": "Vendor Name", "field_type": "text", "required": true, "location_hint": "Company name at the top or in the header"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "customer_name", "display_name": "Customer Name", "field_type": "text", "required": true, "location_hint": "In the Bill To section"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "currency", "display_name": "Currency", "field_type": "text", "default_value": "USD", "allowed_values": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF"]}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "subtotal", "display_name": "Subtotal", "field_type": "currency"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "tax_amount", "display_name": "Tax Amount", "field_type": "currency"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "total_amount", "display_name": "Total Amount", "field_type": "currency", "required": true, "location_hint": "Usually the largest/boldest number on the document"}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "line_items",
    "display_name": "Line Items",
    "field_type": "table",
    "description": "Individual items or services billed",
    "required": true,
    "table_columns": [
      {"code": "description", "display_name": "Description", "field_type": "text"},
      {"code": "quantity", "display_name": "Quantity", "field_type": "number"},
      {"code": "unit_price", "display_name": "Unit Price", "field_type": "currency"},
      {"code": "amount", "display_name": "Line Total", "field_type": "currency"}
    ]
  }'
```

### 5.2b Assign Default Fields to Document Type

```bash
curl -X PUT "http://localhost:8080/api/v1/intellidoc/document-types/${INVOICE_TYPE_ID}/default-fields" \
  -H "Content-Type: application/json" \
  -d '{
    "field_codes": [
      "invoice_number", "invoice_date", "due_date", "vendor_name",
      "customer_name", "currency", "subtotal", "tax_amount",
      "total_amount", "line_items"
    ]
  }'
```

### 5.3 Create Validators

```bash
# Validator 1: Total = Subtotal + Tax
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_total_check",
    "name": "Invoice Total Verification",
    "description": "Verify that total_amount equals subtotal plus tax_amount",
    "validator_type": "cross_field",
    "severity": "warning",
    "config": {
      "type": "sum",
      "fields": ["subtotal", "tax_amount"],
      "total_field": "total_amount",
      "tolerance": 0.01
    },
    "applicable_natures": ["financial"]
  }'

# Validator 2: Invoice date must be before due date
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_date_order",
    "name": "Invoice Date Order",
    "description": "Verify that invoice_date is before or equal to due_date",
    "validator_type": "cross_field",
    "severity": "warning",
    "config": {
      "type": "date_order",
      "fields": ["invoice_date", "due_date"]
    },
    "applicable_natures": ["financial"]
  }'

# Validator 3: Require at least one line item
curl -X POST http://localhost:8080/api/v1/intellidoc/validators \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_has_line_items",
    "name": "Line Items Present",
    "description": "Invoice must have at least one line item",
    "validator_type": "completeness",
    "severity": "error",
    "config": {
      "type": "required_fields",
      "required_fields": ["line_items"]
    },
    "applicable_natures": ["financial"]
  }'
```

### 5.4 Assign Validators to the Document Type

```bash
VALIDATOR_1_ID="<id-from-total-check>"
VALIDATOR_2_ID="<id-from-date-order>"
VALIDATOR_3_ID="<id-from-line-items>"

curl -X POST "http://localhost:8080/api/v1/intellidoc/document-types/${INVOICE_TYPE_ID}/validators" \
  -H "Content-Type: application/json" \
  -d "{
    \"validator_ids\": [\"${VALIDATOR_1_ID}\", \"${VALIDATOR_2_ID}\", \"${VALIDATOR_3_ID}\"]
  }"
```

## Step 6: Process a Document

### Synchronous Processing

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/path/to/sample-invoice.pdf",
    "filename": "sample-invoice.pdf"
  }'
```

The response contains the complete result:
```json
{
  "job_id": "abc-123-...",
  "status": "completed",
  "message": "Processing completed.",
  "result": {
    "job": { ... },
    "documents": [
      {
        "document_type_code": "invoice",
        "classification_confidence": 0.95,
        "extracted_fields": {
          "invoice_number": "INV-2026-0042",
          "invoice_date": "2026-01-15",
          "vendor_name": "Acme Corp",
          "total_amount": 1250.00,
          "line_items": [
            {"description": "Widget A", "quantity": 10, "unit_price": 100.00, "amount": 1000.00},
            {"description": "Widget B", "quantity": 5, "unit_price": 50.00, "amount": 250.00}
          ]
        },
        "is_valid": true,
        "validation_score": 1.0,
        "overall_confidence": "high"
      }
    ],
    "total_fields_extracted": 12,
    "total_validations_passed": 3,
    "total_validations_failed": 0,
    "overall_confidence": "high"
  }
}
```

### Asynchronous Processing

For large files or batch processing, use async mode:

```bash
# Submit
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "url",
    "source_reference": "https://example.com/large-document.pdf",
    "filename": "large-document.pdf",
    "async_mode": true
  }'
```

Response:
```json
{
  "job_id": "def-456-...",
  "status": "pending",
  "message": "Processing job accepted. Poll for status."
}
```

### With Target Schema Override

Override the default fields at request time:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/path/to/sample-invoice.pdf",
    "filename": "sample-invoice.pdf",
    "target_schema": {
      "field_codes": ["invoice_number", "total_amount", "vendor_name"]
    }
  }'
```

Only the specified fields will be extracted, ignoring the document type defaults.

Poll for status:
```bash
# Lightweight status endpoint (optimized for polling)
curl http://localhost:8080/api/v1/intellidoc/jobs/def-456-.../status
```

```json
{
  "job_id": "def-456-...",
  "status": "extracting",
  "current_step": "extract",
  "progress_percent": 65.0,
  "documents_processed": 2,
  "documents_succeeded": 2,
  "documents_failed": 0,
  "total_documents_detected": 3
}
```

When complete, retrieve the result:
```bash
curl http://localhost:8080/api/v1/intellidoc/results/def-456-...
```

## Step 7: Batch Processing

Process multiple files at once:

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/process/batch \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "source_type": "local",
        "source_reference": "/invoices/invoice-001.pdf",
        "filename": "invoice-001.pdf"
      },
      {
        "source_type": "local",
        "source_reference": "/invoices/invoice-002.pdf",
        "filename": "invoice-002.pdf"
      },
      {
        "source_type": "url",
        "source_reference": "https://partner.example.com/invoice-003.pdf",
        "filename": "invoice-003.pdf"
      }
    ],
    "stop_on_failure": false
  }'
```

## Step 8: Export Results

```bash
# JSON export
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}/export?format=json

# CSV export
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}/export?format=csv

# Extracted data only (for downstream integrations)
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}/extracted-data
```

## Step 9: Monitor with Analytics

```bash
# Processing summary
curl "http://localhost:8080/api/v1/intellidoc/analytics/summary?from_date=2026-01-01T00:00:00"

# Breakdown by document type
curl http://localhost:8080/api/v1/intellidoc/analytics/by-document-type

# Top validation failures
curl http://localhost:8080/api/v1/intellidoc/analytics/validation-failures?limit=5

# Cost analysis
curl "http://localhost:8080/api/v1/intellidoc/analytics/cost?group_by=week"
```

## Next Steps

- Read the [Architecture Guide](architecture.md) for design details
- See the [API Reference](api-reference.md) for all endpoints
- Check [Configuration Reference](configuration.md) for all properties
- Browse [Examples](examples.md) for more document type setups
- Add cloud storage with the `s3`, `azure`, or `gcs` extras
- Add PostgreSQL persistence with the `postgresql` extra
- Enable visual splitting for multi-document files
