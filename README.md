# fireflyframework-intellidoc

**Intelligent Document Processing framework powered by Vision-Language Models.**

Built on [pyfly](https://github.com/fireflyframework/pyfly) and [fireflyframework-genai](https://github.com/fireflyframework/fireflyframework-genai).

> Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0

---

## Overview

fireflyframework-intellidoc is a production-grade, catalog-driven Intelligent Document Processing (IDP)
framework. It uses Vision-Language Models (VLMs) instead of traditional OCR to understand, classify,
extract data from, and validate documents of any type.

Everything is runtime-configurable: document types, field definitions, validation rules, and
processing strategies are managed through REST APIs — no code changes or redeployments needed to
support new document types.

## Key Features

### Catalog-Driven Design
- Define document types, field definitions, and validators at runtime via REST APIs
- No code changes needed to add support for new document types
- Visual descriptions and classification cues guide VLM understanding
- Reusable fields catalog with 12 field types and embedded validation rules
- Composable validation rules with 9 validator types

### VLM-First Processing
- Send document page images directly to Vision-Language Models
- No OCR dependency — works with handwritten, poor-quality, and complex-layout documents
- VLM-powered document boundary detection for multi-document files
- VLM-powered visual validation (signature, stamp, photo, watermark detection)
- Field-driven structured extraction with confidence scores

### Complete Processing Pipeline
```
Ingest → Preprocess → Split → Classify → Extract → Validate → Persist
```
- **Ingest**: Local files, URLs, S3, Azure Blob, GCS
- **Preprocess**: PDF→images, rotation correction, enhancement, quality scoring
- **Split**: Page-based or VLM-powered visual boundary detection
- **Classify**: Catalog-driven classification with confidence thresholds
- **Extract**: Catalog-driven field extraction with 12 field types
- **Validate**: Format, cross-field, visual, business rule, completeness checks
- **Persist**: Results stored with full audit trail

### Enterprise Features
- Sync and async processing modes
- Batch processing with stop-on-failure
- Job tracking with progress polling
- Webhook callbacks on completion
- Multi-tenancy support
- Result export (JSON, CSV)
- Analytics and cost tracking
- Domain events for observability
- Health and readiness endpoints

### Hexagonal Architecture
- All infrastructure behind Protocol-based ports
- Swap storage, ingestion, or persistence adapters without changing business logic
- Built on pyfly's DI container with auto-configuration
- Entry-point-based auto-discovery

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        REST API Layer                               │
│  DocumentTypeController · FieldController · ValidatorController     │
│  JobController · ResultController · AnalyticsController · Health    │
├─────────────────────────────────────────────────────────────────────┤
│                     Application Services                            │
│  CatalogService · IngestionService · PreProcessingService           │
│  SplittingService · ClassificationService · ExtractionService       │
│  ValidationService · ResultService · ProcessingOrchestrator         │
├─────────────────────────────────────────────────────────────────────┤
│                       Domain Models                                 │
│  DocumentType · CatalogField · ValidatorDefinition                  │
│  ProcessingJob · DocumentResult · ProcessingResult                  │
├─────────────────────────────────────────────────────────────────────┤
│                     Port Interfaces                                 │
│  FileSourcePort · DocumentStoragePort · DocumentSplitterPort        │
│  ClassifierPort · ExtractorPort · ValidatorPort · ResultStoragePort │
├─────────────────────────────────────────────────────────────────────┤
│                    Adapter Implementations                          │
│  Local/URL/S3/Azure/GCS · PageBased/Visual · Format/CrossField/... │
├─────────────────────────────────────────────────────────────────────┤
│                   Framework Foundation                              │
│              pyfly (DI, Web, Data, Security)                        │
│           fireflyframework-genai (Agents, Pipeline)                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Core (minimal dependencies)
pip install fireflyframework-intellidoc

# With cloud storage support
pip install "fireflyframework-intellidoc[s3,azure,gcs]"

# With PostgreSQL persistence
pip install "fireflyframework-intellidoc[postgresql,web]"

# With everything
pip install "fireflyframework-intellidoc[all]"

# Development (includes testing, linting, type-checking)
pip install "fireflyframework-intellidoc[dev]"
```

### Optional Dependencies

| Extra | Description |
|-------|-------------|
| `pdf-images` | PDF to image conversion (requires system poppler) |
| `ocr` | OCR fallback via pytesseract |
| `barcode` | Barcode/QR code detection |
| `s3` | Amazon S3 ingestion and storage |
| `azure` | Azure Blob Storage support |
| `gcs` | Google Cloud Storage support |
| `postgresql` | PostgreSQL persistence |
| `mongodb` | MongoDB persistence |
| `web` | Web server (Starlette/Uvicorn) |
| `messaging` | Kafka/RabbitMQ async jobs |
| `observability` | Prometheus metrics, tracing |
| `security` | Authentication and RBAC |
| `all` | All of the above |
| `dev` | Development tools (pytest, ruff, pyright) |

## Quick Start

### 1. Create a pyfly Application

```python
from pyfly.core import PyFlyApplication, pyfly_application


@pyfly_application(
    name="my-idp-service",
    scan_packages=["myapp", "fireflyframework_intellidoc"],
)
class MyIDPApp:
    pass


app = PyFlyApplication(MyIDPApp)
```

### 2. Configure IntelliDoc

```yaml
# application.yml
pyfly:
  intellidoc:
    enabled: true
    default_model: "openai:gpt-4o"
    storage_provider: "local"
    storage_local_path: "/var/intellidoc/storage"
    ingestion_local_enabled: true
    ingestion_url_enabled: true
```

### 3. Create a Document Type

```bash
curl -X POST http://localhost:8080/api/v1/intellidoc/document-types \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice",
    "name": "Invoice",
    "description": "Commercial invoice for goods or services",
    "nature": "financial",
    "visual_description": "A document with line items, totals, and payment details",
    "visual_cues": ["company logo", "invoice number", "line items table", "total amount"],
    "sample_keywords": ["invoice", "bill to", "total", "due date", "payment terms"]
  }'
```

### 4. Create Catalog Fields

```bash
# Create reusable field definitions
curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice_number",
    "display_name": "Invoice Number",
    "field_type": "text",
    "required": true,
    "validation_rules": [
      {"rule_type": "format", "config": {"pattern": "^INV-\\d+$"}, "message": "Must match INV-XXXX format"}
    ]
  }'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "invoice_date", "display_name": "Invoice Date", "field_type": "date", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "total_amount", "display_name": "Total Amount", "field_type": "currency", "required": true}'

curl -X POST http://localhost:8080/api/v1/intellidoc/fields \
  -H "Content-Type: application/json" \
  -d '{"code": "vendor_name", "display_name": "Vendor Name", "field_type": "text", "required": true}'

# Assign default fields to the document type
curl -X PUT "http://localhost:8080/api/v1/intellidoc/document-types/{id}/default-fields" \
  -H "Content-Type: application/json" \
  -d '{"field_codes": ["invoice_number", "invoice_date", "total_amount", "vendor_name"]}'
```

### 5. Process a Document

```bash
# Synchronous processing
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/path/to/invoice.pdf",
    "filename": "invoice.pdf"
  }'

# Asynchronous processing
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "url",
    "source_reference": "https://example.com/invoice.pdf",
    "filename": "invoice.pdf",
    "async_mode": true
  }'

# Process with custom field selection (target_schema)
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/path/to/invoice.pdf",
    "filename": "invoice.pdf",
    "target_schema": {
      "field_codes": ["invoice_number", "total_amount"]
    }
  }'

# Poll for status
curl http://localhost:8080/api/v1/intellidoc/jobs/{job_id}/status
```

### 6. Retrieve Results

```bash
# Full result
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}

# Extracted data only (for integrations)
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}/extracted-data

# Export as CSV
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}/export?format=csv
```

## API Overview

| Area | Prefix | Endpoints | Description |
|------|--------|-----------|-------------|
| Document Types | `/api/v1/intellidoc/document-types` | 9 | CRUD, default fields, validator assignment |
| Fields | `/api/v1/intellidoc/fields` | 6 | CRUD, lookup by code |
| Validators | `/api/v1/intellidoc/validators` | 7 | CRUD, type listing, testing |
| Processing | `/api/v1/intellidoc/process` | 3 | Submit documents, batch, sources |
| Jobs | `/api/v1/intellidoc/jobs` | 4 | List, detail, status polling, cancel |
| Results | `/api/v1/intellidoc/results` | 5 | Full result, document detail, export |
| Analytics | `/api/v1/intellidoc/analytics` | 5 | Summary, by-type, by-nature, cost |
| Health | `/api/v1/intellidoc/health` | 4 | Health, readiness, config, metrics |
| **Total** | | **43** | |

## Configuration

All properties use the `pyfly.intellidoc.*` prefix and can be set via YAML config
or environment variables (`PYFLY_INTELLIDOC_*`).

| Property | Default | Description |
|----------|---------|-------------|
| `enabled` | `true` | Enable/disable IntelliDoc |
| `default_model` | `openai:gpt-4o` | Default VLM model |
| `max_file_size_mb` | `100` | Maximum file size |
| `max_pages_per_file` | `500` | Maximum pages per file |
| `default_splitting_strategy` | `visual` | `page_based` or `visual` |
| `default_confidence_threshold` | `0.7` | Classification confidence threshold |
| `storage_provider` | `local` | `local`, `s3`, `azure_blob`, `gcs` |
| `async_processing_enabled` | `true` | Enable async processing mode |

See [docs/configuration.md](docs/configuration.md) for the complete reference.

## Documentation

- [Architecture Guide](docs/architecture.md) — Design principles, layers, and data flow
- [Getting Started](docs/getting-started.md) — Step-by-step tutorial
- [API Reference](docs/api-reference.md) — Complete endpoint documentation
- [Configuration Reference](docs/configuration.md) — All configuration properties
- [Examples](docs/examples.md) — Invoice, identity document, batch processing examples

## Module Structure

```
fireflyframework_intellidoc/
├── __init__.py                    # Public API exports
├── _version.py                    # Version string
├── auto_configuration.py          # Master auto-configuration
├── config.py                      # IntelliDocConfig (60+ properties)
├── exceptions.py                  # Exception hierarchy
├── types.py                       # Shared enums and value types
├── catalog/                       # Document type & validator catalog
│   ├── domain/                    # Domain models
│   ├── exposure/                  # REST controllers & DTOs
│   ├── ports/                     # Port interfaces
│   └── service.py                 # CatalogService
├── ingestion/                     # File ingestion
│   ├── adapters/                  # Local, URL, S3, Azure, GCS
│   ├── ports/                     # FileSourcePort
│   ├── auto_configuration.py
│   └── service.py                 # IngestionService
├── preprocessing/                 # Document preprocessing
│   ├── ports/                     # PreProcessorPort
│   ├── page_extractor.py          # PDF → page images
│   ├── rotation.py                # Rotation detection & correction
│   ├── enhancer.py                # Image enhancement
│   ├── quality.py                 # Quality scoring
│   └── service.py                 # PreProcessingService
├── splitting/                     # Document splitting
│   ├── strategies/                # PageBased, Visual
│   ├── ports/                     # DocumentSplitterPort
│   └── service.py                 # SplittingService
├── classification/                # Document classification
│   ├── agents/                    # DocumentClassifierAgent (VLM)
│   ├── ports/                     # ClassifierPort
│   └── service.py                 # ClassificationService
├── extraction/                    # Data extraction
│   ├── agents/                    # FieldExtractorAgent (VLM)
│   ├── ports/                     # ExtractorPort
│   └── service.py                 # ExtractionService
├── validation/                    # Document validation
│   ├── validators/                # Format, CrossField, Visual, BusinessRule, Completeness
│   ├── ports/                     # ValidatorPort
│   ├── engine.py                  # ValidationEngine
│   └── service.py                 # ValidationService
├── pipeline/                      # Processing pipeline
│   ├── steps/                     # 7 pipeline steps
│   ├── exposure/                  # ProcessingController, HealthController
│   ├── context.py                 # IDPPipelineContext
│   ├── orchestrator.py            # ProcessingOrchestrator
│   └── webhooks.py                # WebhookService
├── results/                       # Job tracking & results
│   ├── domain/                    # ProcessingJob, ProcessingResult
│   ├── exposure/                  # JobController, ResultController, AnalyticsController
│   ├── ports/                     # ResultStoragePort
│   └── service.py                 # ResultService
├── storage/                       # Document storage
│   ├── adapters/                  # Local, S3, Azure, GCS
│   ├── ports/                     # DocumentStoragePort
│   └── auto_configuration.py
└── observability/                 # Observability
    ├── events.py                  # Domain events
    └── metrics.py                 # MetricsCollector
```

## Requirements

- Python >= 3.13
- pyfly >= 0.1.0
- fireflyframework-genai >= 26.02.06

## License

Apache License 2.0 — Copyright 2026 Firefly Software Solutions Inc

See [LICENSE](LICENSE) for the full text.
