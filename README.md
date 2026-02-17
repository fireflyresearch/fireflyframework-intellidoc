<p align="center">
  <img src="docs/images/logo.png" alt="IntelliDoc" width="500">
</p>

<p align="center">
  <strong>Intelligent Document Processing framework powered by Vision-Language Models</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-%3E%3D3.13-blue?logo=python&logoColor=white" alt="Python 3.13+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"></a>
  <a href="https://github.com/fireflyframework/fireflyframework-intellidoc/releases"><img src="https://img.shields.io/badge/version-26.02.02-orange" alt="Version"></a>
</p>

---

## Overview

fireflyframework-intellidoc is a production-grade, catalog-driven Intelligent Document Processing (IDP)
framework. It uses Vision-Language Models (VLMs) instead of traditional OCR to understand, classify,
extract data from, and validate documents of any type.

Everything is runtime-configurable: document types, field definitions, validation rules, and
processing strategies are managed through REST APIs — no code changes or redeployments needed to
support new document types.

Built on [pyfly](https://github.com/fireflyframework/pyfly) and [fireflyframework-genai](https://github.com/fireflyframework/fireflyframework-genai).

## Key Features

<table>
<tr>
<td width="50%" valign="top">

### Catalog-Driven Design
- Define document types, fields, and validators at runtime via REST APIs
- Reusable fields catalog with 12 field types and embedded validation rules
- Visual descriptions and classification cues guide VLM understanding
- Composable validation rules with 9 validator types

</td>
<td width="50%" valign="top">

### VLM-First Processing
- Send document page images directly to Vision-Language Models
- No OCR dependency — works with handwritten, poor-quality, and complex-layout documents
- VLM-powered visual validation (signature, stamp, photo, watermark detection)
- Field-driven structured extraction with confidence scores

</td>
</tr>
<tr>
<td width="50%" valign="top">

### Enterprise Ready
- Sync and async processing modes with batch support
- Job tracking with progress polling and webhook callbacks
- Multi-tenancy, result export (JSON, CSV), analytics and cost tracking
- Health and readiness endpoints

</td>
<td width="50%" valign="top">

### Hexagonal Architecture
- All infrastructure behind Protocol-based ports
- Swap storage, ingestion, or persistence adapters without touching business logic
- Built on pyfly's DI container with auto-configuration
- Entry-point-based auto-discovery

</td>
</tr>
</table>

## Processing Pipeline

```
Ingest → Preprocess → Split → Classify → Extract → Validate → Persist
```

| Stage | Description |
|-------|-------------|
| **Ingest** | Local files, URLs, S3, Azure Blob, GCS |
| **Preprocess** | PDF to images, rotation correction, enhancement, quality scoring |
| **Split** | Page-based or VLM-powered visual boundary detection |
| **Classify** | Catalog-driven classification with confidence thresholds |
| **Extract** | Catalog-driven field extraction with 12 field types |
| **Validate** | Format, cross-field, visual, business rule, completeness checks |
| **Persist** | Results stored with full audit trail |

## Installation

### One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/fireflyframework/fireflyframework-intellidoc/main/install.sh | bash
```

The interactive installer guides you through:
- Python and system dependency checks
- VLM provider selection and API key setup
- Storage backend configuration
- Optional extras (cloud storage, PostgreSQL, observability, security)
- Automatic `pyfly.yaml` and `.env` generation

### Manual Install

```bash
pip install "fireflyframework-intellidoc[web]"
```

See the extras table below for all available packages.

<details>
<summary><strong>Installation extras</strong></summary>

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

</details>

## Quick Start

### 1. Install and Configure

```bash
pip install "fireflyframework-intellidoc[web]"
```

Create `pyfly.yaml`:

```yaml
pyfly:
  app:
    module: fireflyframework_intellidoc.main:app
  intellidoc:
    enabled: true
    default_model: "openai:gpt-4o"
    storage_provider: "local"
    storage_local_path: "./intellidoc-storage"
```

```bash
export OPENAI_API_KEY="sk-..."
pyfly run
```

No application class needed — IntelliDoc ships with a built-in entry point.

### 2. Create a Document Type

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

### 3. Create Catalog Fields

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

# Assign default fields to the document type
curl -X PUT "http://localhost:8080/api/v1/intellidoc/document-types/{id}/default-fields" \
  -H "Content-Type: application/json" \
  -d '{"field_codes": ["invoice_number", "invoice_date", "total_amount"]}'
```

### 4. Process a Document

```bash
# Synchronous processing
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "local",
    "source_reference": "/path/to/invoice.pdf",
    "filename": "invoice.pdf"
  }'

# With custom field selection (target_schema)
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

# Async mode — returns job ID for polling
curl -X POST http://localhost:8080/api/v1/intellidoc/process \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "url",
    "source_reference": "https://example.com/invoice.pdf",
    "filename": "invoice.pdf",
    "async_mode": true
  }'
```

### 5. Retrieve Results

```bash
# Full result
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}

# Extracted data only
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}/extracted-data

# Export as CSV
curl http://localhost:8080/api/v1/intellidoc/results/{job_id}/export?format=csv
```

## API Overview

| Area | Prefix | Endpoints | Description |
|------|--------|:---------:|-------------|
| Document Types | `/api/v1/intellidoc/document-types` | 9 | CRUD, default fields, validator assignment |
| Fields | `/api/v1/intellidoc/fields` | 6 | CRUD, lookup by code |
| Validators | `/api/v1/intellidoc/validators` | 7 | CRUD, type listing, testing |
| Processing | `/api/v1/intellidoc/process` | 3 | Submit documents, batch, sources |
| Jobs | `/api/v1/intellidoc/jobs` | 4 | List, detail, status polling, cancel |
| Results | `/api/v1/intellidoc/results` | 5 | Full result, document detail, export |
| Analytics | `/api/v1/intellidoc/analytics` | 5 | Summary, by-type, by-nature, cost |
| Health | `/api/v1/intellidoc/health` | 4 | Health, readiness, config, metrics |
| **Total** | | **43** | |

## Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                            REST API Layer                             │
│  DocumentTypeController · FieldController · ValidatorController       │
│  JobController · ResultController · AnalyticsController · Health      │
├───────────────────────────────────────────────────────────────────────┤
│                         Application Services                          │
│  CatalogService · IngestionService · PreProcessingService             │
│  SplittingService · ClassificationService · ExtractionService         │
│  ValidationService · ResultService · ProcessingOrchestrator           │
├───────────────────────────────────────────────────────────────────────┤
│                             Domain Models                             │
│  DocumentType · CatalogField · ValidatorDefinition                    │
│  ProcessingJob · DocumentResult · ProcessingResult                    │
├───────────────────────────────────────────────────────────────────────┤
│                            Port Interfaces                            │
│  FileSourcePort · DocumentStoragePort · DocumentSplitterPort          │
│  ClassifierPort · ExtractorPort · ValidatorPort · ResultStoragePort   │
├───────────────────────────────────────────────────────────────────────┤
│                        Adapter Implementations                        │
│  Local/URL/S3/Azure/GCS · PageBased/Visual · Format/CrossField/...   │
├───────────────────────────────────────────────────────────────────────┤
│                         Framework Foundation                          │
│                    pyfly (DI, Web, Data, Security)                    │
│                 fireflyframework-genai (Agents, Pipeline)             │
└───────────────────────────────────────────────────────────────────────┘
```

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

| Document | Description |
|----------|-------------|
| [Architecture Guide](docs/architecture.md) | Design principles, layers, and data flow |
| [Getting Started](docs/getting-started.md) | Step-by-step tutorial |
| [API Reference](docs/api-reference.md) | Complete endpoint documentation |
| [Configuration Reference](docs/configuration.md) | All configuration properties |
| [Deploy Guide](docs/deploy.md) | Production deployment (Docker, systemd, scaling) |
| [Examples](docs/examples.md) | Invoice, identity document, batch processing examples |

<details>
<summary><strong>Module structure</strong></summary>

```
fireflyframework_intellidoc/
├── __init__.py                    # Public API exports
├── _version.py                    # Version string
├── main.py                        # Built-in ASGI entry point (pyfly run)
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

</details>

## Requirements

- Python >= 3.13
- pyfly >= 0.1.0
- fireflyframework-genai >= 26.02.06

## License

Apache License 2.0 — Copyright 2026 Firefly Software Solutions Inc

See [LICENSE](LICENSE) for the full text.
