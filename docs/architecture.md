# Architecture Guide

**fireflyframework-intellidoc — Intelligent Document Processing Framework**

> Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0

---

## Design Philosophy

fireflyframework-intellidoc follows three core design principles:

1. **VLM-First** — Send document images directly to Vision-Language Models instead of relying on traditional OCR pipelines. This provides superior understanding of layout, handwriting, and visual elements.

2. **Catalog-Driven** — All document types, field definitions, and validation rules are runtime-configurable through REST APIs. Adding support for a new document type requires zero code changes.

3. **Hexagonal Architecture** — All infrastructure (storage, AI models, databases) sits behind Protocol-based port interfaces. Adapters can be swapped without touching business logic.

## Layered Architecture

The framework is organized into six layers, from outermost to innermost:

```
┌──────────────────────────────────────────────────────────────┐
│  1. Exposure Layer (REST Controllers + DTOs)                 │
├──────────────────────────────────────────────────────────────┤
│  2. Application Services (Orchestration + Business Logic)    │
├──────────────────────────────────────────────────────────────┤
│  3. Domain Models (Entities + Value Objects)                 │
├──────────────────────────────────────────────────────────────┤
│  4. Port Interfaces (Protocol-based contracts)               │
├──────────────────────────────────────────────────────────────┤
│  5. Adapter Implementations (Infrastructure)                 │
├──────────────────────────────────────────────────────────────┤
│  6. Auto-Configuration (Wiring + Conditional Registration)   │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1: Exposure Layer

The exposure layer provides two entry points into the framework:

**REST API** — Controllers expose the framework's capabilities as HTTP endpoints. Each controller
handles request/response mapping, validation, and delegation to application services.

**Controllers:**
- `DocumentTypeController` — CRUD for document type catalog
- `FieldController` — CRUD for fields catalog
- `ValidatorController` — CRUD for validator catalog
- `ProcessingController` — Document submission (sync/async/batch)
- `JobController` — Job listing, tracking, cancellation
- `ResultController` — Result retrieval, document details, export
- `AnalyticsController` — Aggregated statistics and cost analysis
- `IntelliDocHealthController` — Health, readiness, config, metrics

**DTOs** are Pydantic `BaseModel` classes that define the API contract. They are
intentionally separate from domain models — input validation and response shaping
stay at the boundary.

**CLI** — The `intellidoc` command-line tool provides an alternative entry point using
pyfly's `@shell_component` infrastructure. CLI commands (`process`, `batch`, `catalog`)
call the same `ProcessingOrchestrator` directly, bypassing the REST layer.

**Shell Components:**
- `ProcessCommands` — `process` (single file) and `batch` (directory) commands
- `CatalogCommands` — `catalog validate` and `catalog show` commands

The CLI boots the same PyFly DI container as the web server but swaps in-memory adapters
for catalog and result storage, loading document types from `catalog.yaml` instead of a
database. See the [CLI Reference](cli.md) for usage.

### Layer 2: Application Services

Services implement business logic and orchestrate port interactions. They are
annotated with pyfly's `@service` stereotype for auto-discovery.

| Service | Responsibility |
|---------|---------------|
| `CatalogService` | Document type, validator, and field catalog CRUD with business rules |
| `IngestionService` | Multi-adapter file ingestion with type/size validation |
| `PreProcessingService` | Page extraction, rotation, enhancement, quality assessment |
| `SplittingService` | Strategy-based document splitting |
| `ClassificationService` | VLM-powered classification with confidence thresholds |
| `ExtractionService` | Field-driven extraction via VLM |
| `ValidationService` | Catalog-driven validation engine orchestration |
| `ResultService` | Job lifecycle management and result aggregation |
| `ProcessingOrchestrator` | Full pipeline orchestration with per-document fan-out |
| `WebhookService` | Job completion callbacks with HMAC signatures |

### Layer 3: Domain Models

Pure Pydantic models representing the business domain. No framework dependencies.

**Catalog Domain:**
- `DocumentType` — A type of document the system can process (e.g., "Invoice", "Passport")
- `CatalogField` — A reusable field definition with type, constraints, location hints, and embedded validation rules
- `FieldValidationRule` — An embedded validation rule on a catalog field
- `ValidatorDefinition` — A standalone validation rule with type, severity, and applicability rules

**Processing Domain:**
- `ProcessingJob` — Tracks the lifecycle of a file submission
- `DocumentResult` — Processing outcome for a single detected document
- `ProcessingResult` — Aggregate result for a job (all documents + summary)
- `ValidationResult` — Outcome of a single validation check

**Pipeline Models:**
- `PreProcessingResult` — Page images with quality scores
- `SplittingResult` — Detected document boundaries
- `ClassificationResult` — Classification candidates with confidence
- `ExtractionResult` — Extracted fields with per-field confidence

### Layer 4: Port Interfaces

Ports are `@runtime_checkable Protocol` classes defining contracts between
the domain and infrastructure layers.

```python
@runtime_checkable
class FileSourcePort(Protocol):
    async def supports(self, source_type: str) -> bool: ...
    async def fetch(self, source_reference: str, ...) -> FileReference: ...
```

**Defined Ports:**

| Port | Purpose |
|------|---------|
| `FileSourcePort` | Fetch files from various sources |
| `DocumentStoragePort` | Store processed documents and pages |
| `DocumentSplitterPort` | Split multi-document files |
| `ClassifierPort` | Classify documents by type |
| `ExtractorPort` | Extract structured data |
| `ValidatorPort` | Validate extracted data |
| `DocumentTypeCatalogPort` | Persist document type catalog |
| `FieldCatalogPort` | Persist field catalog |
| `ValidatorCatalogPort` | Persist validator catalog |
| `ResultStoragePort` | Persist jobs and results |

### Layer 5: Adapter Implementations

Concrete implementations of port interfaces for specific technologies.

**Ingestion Adapters:**
- `LocalFileSourceAdapter` — Filesystem reads
- `UrlFileSourceAdapter` — HTTP/HTTPS downloads via httpx
- `S3FileSourceAdapter` — Amazon S3 via aioboto3
- `AzureBlobFileSourceAdapter` — Azure Blob via azure-storage-blob
- `GCSFileSourceAdapter` — Google Cloud Storage via gcloud-aio-storage

**Storage Adapters:**
- `LocalDocumentStorageAdapter` — Local filesystem
- `S3DocumentStorageAdapter` — Amazon S3
- `AzureBlobDocumentStorageAdapter` — Azure Blob Storage
- `GCSDocumentStorageAdapter` — Google Cloud Storage

**Splitting Strategies:**
- `PageBasedSplitter` — Each page = one document
- `VisualSplitter` — VLM-powered boundary detection

**VLM Agents (via fireflyframework-genai):**
- `DocumentClassifierAgent` — Catalog-driven classification
- `FieldExtractorAgent` — Field-driven extraction

**Validation Handlers:**
- `FormatValidator` — Email, phone, IBAN, regex patterns, numeric range, checksum
- `CrossFieldValidator` — Field matching, sum verification, date ordering
- `VisualValidator` — VLM-based visual checks (signatures, stamps, etc.)
- `BusinessRuleValidator` — Expression evaluation, reference data lookup
- `CompletenessValidator` — Required fields, minimum pages, field percentage

**Validation Engine** (`ValidationEngine`) is the dispatcher that routes each
`ValidatorDefinition` to the appropriate handler based on its `validator_type`.
Key design guarantee: the engine **never raises** — if a handler throws an exception
or no handler is registered for a type, the engine captures the error as a synthetic
failed `ValidationResult` and continues to the next validator. This ensures all
validators run regardless of individual failures.

### Layer 6: Auto-Configuration

pyfly's `@configuration` classes with `@conditional_on_property` conditions
wire everything together based on the application's configuration.

- `IntelliDocAutoConfiguration` — Master config, splitters, validators, metrics
- `IngestionAutoConfiguration` — Conditional ingestion adapters
- `StorageAutoConfiguration` — Storage provider selection
- `IntelliDocCLIAutoConfiguration` — CLI-specific beans: in-memory catalog/result adapters, branded shell adapter (conditional on `pyfly.shell.enabled`)

Auto-configurations are registered via Python entry points:
```toml
[project.entry-points."pyfly.auto_configuration"]
intellidoc = "fireflyframework_intellidoc.auto_configuration:IntelliDocAutoConfiguration"
intellidoc-cli = "fireflyframework_intellidoc.cli.auto_configuration:IntelliDocCLIAutoConfiguration"
```

## Processing Pipeline

The core processing pipeline flows through seven steps:

```
┌──────────┐    ┌──────────────┐    ┌──────────┐
│  Ingest  │───>│  Preprocess  │───>│  Split   │
└──────────┘    └──────────────┘    └──────────┘
                                         │
                            ┌────────────┘
                            │  For each document:
                            ▼
                    ┌──────────────┐    ┌──────────┐
                    │  Classify    │───>│  Extract  │
                    └──────────────┘    └──────────┘
                                             │
                                             ▼
                                    ┌──────────────┐    ┌──────────┐
                                    │  Validate    │───>│  Persist │
                                    └──────────────┘    └──────────┘
```

### Step Details

**1. Ingestion** (`IngestionStep`)
- Resolves the appropriate `FileSourcePort` adapter
- Fetches file content and creates a `FileReference`
- Validates MIME type and file size

**2. Preprocessing** (`PreProcessingStep`)
- Extracts page images from PDFs or passes through images
- Applies rotation correction (EXIF-based)
- Enhances image quality (denoise, contrast, sharpen)
- Computes per-page quality scores

**3. Splitting** (`SplittingStep`)
- Detects document boundaries within multi-page files
- Page-based strategy: each page is a separate document
- Visual strategy: VLM analyzes pages to detect boundaries

**4. Classification** (`ClassificationStep`) — *per document*
- Loads active document types from the catalog
- Builds a dynamic classification prompt from catalog data
- VLM analyzes document pages and returns ranked candidates
- Checks confidence threshold; filters low-confidence matches

**5. Extraction** (`ExtractionStep`) — *per document*
- Uses resolved fields from the context (either from `target_schema` or document type defaults)
- Builds a structured extraction prompt from the field definitions
- VLM extracts all defined fields with per-field confidence
- Applies default values for missing optional fields

**6. Validation** (`ValidationStep`) — *per document*
- Loads applicable validators from the catalog (document-type level)
- Also runs field-level validation rules embedded in `CatalogField` definitions
- Dispatches each validator to the appropriate handler
- Collects `ValidationResult` objects with pass/fail and severity

**7. Persistence** (`PersistenceStep`) — *per document*
- Builds a `DocumentResult` from classification, extraction, and validation
- Computes overall confidence from component scores
- Saves to `ResultStoragePort`

### Orchestration

The `ProcessingOrchestrator` manages the full lifecycle:
- Creates a `ProcessingJob` for tracking
- Runs pipeline steps in sequence
- Handles per-document fan-out (steps 4-7 run for each detected document)
- Resolves target fields between classification and extraction (explicit target_schema > document type defaults)
- Updates job status and progress at each stage
- Supports partial completion (some documents succeed, others fail)
- Provides both sync (`process()`) and async (`submit()`) entry points

## Data Flow

```
                    ┌─────────────┐
                    │ ProcessRequest│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ProcessingJob│  (status: PENDING)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │FileReference │  (from ingestion)
                    └──────┬──────┘
                           │
               ┌───────────▼───────────┐
               │PreProcessingResult    │  (page images + quality)
               └───────────┬───────────┘
                           │
                ┌──────────▼──────────┐
                │ SplittingResult     │  (document boundaries)
                └──────────┬──────────┘
                           │
           ┌───────────────┼───────────────┐
           │ (per doc)     │               │
    ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐
    │Classification│ │Classification│ │    ...     │
    │   Result    │ │   Result    │ │             │
    └──────┬──────┘ └──────┬─────┘ └─────────────┘
           │               │
    ┌──────▼──────┐ ┌──────▼──────┐
    │ Extraction  │ │ Extraction  │
    │   Result    │ │   Result    │
    └──────┬──────┘ └──────┬─────┘
           │               │
    ┌──────▼──────┐ ┌──────▼──────┐
    │ Validation  │ │ Validation  │
    │  Results[]  │ │  Results[]  │
    └──────┬──────┘ └──────┬─────┘
           │               │
    ┌──────▼──────┐ ┌──────▼──────┐
    │ Document    │ │ Document    │
    │   Result    │ │   Result    │
    └──────┬──────┘ └──────┬─────┘
           │               │
           └───────┬───────┘
                   │
            ┌──────▼──────┐
            │ Processing  │
            │   Result    │  (aggregate + summary)
            └─────────────┘
```

## Pipeline Context

The `IDPPipelineContext` is a mutable dataclass that carries all state through the pipeline.
Steps read from it and write to it — this is the single object that threads data between stages.

| Group | Fields | Description |
|---|---|---|
| **Job metadata** | `job_id`, `source_type`, `source_reference`, `filename`, `expected_type`, `expected_nature`, `splitting_strategy`, `tenant_id`, `correlation_id`, `tags` | Immutable after creation — set from `ProcessRequest` |
| **Target schema** | `target_field_codes`, `resolved_fields` | `target_field_codes` is set from the request; `resolved_fields` is populated by the orchestrator after classification |
| **Pipeline results** | `file_reference`, `preprocessing_result`, `splitting_result` | Set once by ingestion, preprocessing, and splitting steps |
| **Per-document cursor** | `current_pages`, `current_doc_index`, `classification_result`, `extraction_result`, `validation_results` | **Mutated in-place** during the per-document fan-out loop — steps must not cache these across iterations |
| **Aggregation** | `document_results` | Accumulated across all fan-out iterations |
| **Observability** | `metadata`, `total_tokens_used`, `total_cost_usd` | `total_tokens_used` and `total_cost_usd` are running accumulators — steps increment them, they are never reset |

The per-document cursor fields (`current_pages`, `classification_result`, etc.) are intentionally
reset by the orchestrator at the start of each document iteration. This in-place mutation design
avoids copying large page image lists and keeps the pipeline simple.

## VLM Prompt Construction

A distinguishing feature of IntelliDoc is how it dynamically builds VLM prompts from
catalog data. This means the same VLM agent can classify any document type and extract
any set of fields — the prompts are assembled at runtime from whatever is in the catalog.

### Classification Prompts

The `DocumentClassifierAgent` builds a classification prompt from all active `DocumentType`
entries. For each type, it renders:

```
- Code: invoice
  Name: Commercial Invoice
  Nature: financial
  Description: A commercial invoice for goods or services rendered...
  Visual: A formal document with a company logo at the top, an invoice number...
  Cues: company logo, invoice number, line items table, total amount
  Keywords: invoice, bill to, total, due date, payment terms
  Instructions: <custom per-type guidance if provided>
```

The prompt concludes with reasoning guidance (consider visual layout, logos, headers,
key content, document nature) and optional hints (`expected_type`, `expected_nature`)
that flow directly from the `ProcessRequest` through the pipeline context into the prompt.

The VLM returns a structured `VLMClassificationOutput` with the best match code,
confidence score, reasoning text, and ranked alternatives. The agent maps codes back
to catalog `DocumentType` objects to build `ClassificationCandidate` results.

### Extraction Prompts

The `FieldExtractorAgent` builds an extraction prompt from a list of resolved `CatalogField`
objects. Each field is rendered conditionally — only non-empty properties appear:

```
- invoice_number (text): Invoice Number
  Description: The unique invoice identifier
  Required: yes
  Location: Usually near the top of the document
  Format: ^INV-\d+$
  Allowed values: <comma-separated list>
  Range: 0.0 to 100000.0
  Table columns:
    - description (text): Description
    - quantity (number): Quantity
    - amount (currency): Line Total
```

Table columns are rendered recursively with increasing indentation, supporting
arbitrarily nested table structures.

The prompt appends fixed extraction rules:
- Only extract information explicitly visible in the document
- If a field cannot be found, set its value to null
- Preserve exact values as they appear (don't reformat)
- For tables, extract all rows as a list of objects
- For each field, provide a confidence score (0.0-1.0)
- Pay attention to field location hints when provided

The VLM returns a structured `VLMExtractionOutput` with `fields` (keyed by code),
`confidence` (per-field scores), and `notes` (free-text observations).

### Prompt-Visible vs Metadata-Only Properties

Not all `CatalogField` properties appear in the VLM prompt:

| Property | In prompt? | Purpose |
|---|:-:|---|
| `code`, `display_name`, `field_type` | Yes | Core field identification |
| `description` | Yes | Semantic context for extraction |
| `required` | Yes | Signals importance to the VLM |
| `location_hint` | Yes | Spatial guidance on the page |
| `format_pattern` | Yes | Expected format/regex |
| `allowed_values` | Yes | Constrains VLM output |
| `min_value`, `max_value` | Yes | Numeric bounds |
| `table_columns` | Yes | Nested column structure |
| `default_value` | No | Applied post-extraction for missing optional fields |
| `validation_rules` | No | Used by `ValidationEngine` after extraction |
| `tags`, `is_active` | No | Catalog management metadata |
| `created_at`, `updated_at` | No | Audit timestamps |

This separation is intentional: the VLM prompt stays focused on extraction guidance,
while validation rules and metadata serve downstream pipeline stages.

## Fields Catalog

The Fields Catalog replaces the previous per-document-type extraction schema with
reusable, self-describing field definitions. Key aspects:

**Reusability** — The same `CatalogField` (e.g., `invoice_number`) can be referenced
by multiple document types via `default_field_codes`.

**Embedded Validation** — Each field carries its own `validation_rules` (format,
range, required checks) so simple validation travels with the field definition.

**Runtime Override** — Users can pass a `target_schema` in the `ProcessRequest`
to specify exactly which fields to extract, overriding document type defaults.

**Resolution Priority:**
1. Explicit `target_schema.field_codes` from the request
2. Document type's `default_field_codes` (fallback after classification)
3. Empty (no extraction performed)

## Integration Points

### pyfly Framework
- **DI Container**: `@service`, `@rest_controller`, `@configuration`, `@bean`
- **Web Layer**: `@request_mapping`, `@get_mapping`, `@post_mapping`, etc.
- **Parameter Binding**: `PathVar[T]`, `QueryParam[T]`, `Body[T]`, `Valid[T]`
- **Conditions**: `@conditional_on_property` for conditional bean registration
- **Auto-Discovery**: Entry-point-based auto-configuration scanning

### fireflyframework-genai
- **FireflyAgent**: Used for VLM interactions (classification, extraction, visual validation, splitting)
- **Structured Output**: Pydantic-based output schemas for VLM responses
- **Agent Templates**: Dynamic prompt building from catalog data

### Observability
- **Domain Events**: Pydantic-based events published at pipeline milestones
- **Metrics**: In-memory counters/gauges with Prometheus-compatible naming
- **Webhooks**: HMAC-signed HTTP callbacks on job completion

## Extensibility

### Adding a New Ingestion Source
1. Implement `FileSourcePort` protocol
2. Register via `@bean` in a `@configuration` class
3. Guard with `@conditional_on_property`

### Adding a New Validator Type
1. Implement `ValidatorPort` protocol
2. Register as a `@bean` in auto-configuration
3. Add the type to `ValidatorType` enum
4. The `ValidationEngine` will automatically dispatch to it

### Adding a New Splitting Strategy
1. Implement `DocumentSplitterPort` protocol
2. Register as a `@bean`
3. Reference by name in the `splitting_strategy` parameter

### Supporting a New Document Type
No code needed — use the REST API:
1. `POST /api/v1/intellidoc/document-types` — Create the type with visual cues
2. `POST /api/v1/intellidoc/fields` — Create reusable field definitions (or reuse existing ones)
3. `PUT /api/v1/intellidoc/document-types/{id}/default-fields` — Assign default fields
4. `POST /api/v1/intellidoc/document-types/{id}/validators` — Assign validators
5. Submit documents — they will be automatically classified and processed

## Error Handling

IntelliDoc defines a structured exception hierarchy rooted at `IntelliDocException`. Every exception carries:
- `message` — Human-readable description
- `code` — Machine-readable error code (e.g., `FIELD_NOT_FOUND`)
- `context` — Dictionary of additional metadata

The hierarchy is organized by pipeline stage:

```
IntelliDocException
├── CatalogException
│   ├── DocumentTypeNotFoundException (DOCUMENT_TYPE_NOT_FOUND)
│   ├── DocumentTypeAlreadyExistsException (DOCUMENT_TYPE_DUPLICATE)
│   ├── FieldNotFoundException (FIELD_NOT_FOUND)
│   ├── FieldAlreadyExistsException (FIELD_DUPLICATE)
│   ├── ValidatorNotFoundException (VALIDATOR_NOT_FOUND)
│   ├── ValidatorAlreadyExistsException (VALIDATOR_DUPLICATE)
│   └── TargetSchemaResolutionException (TARGET_SCHEMA_RESOLUTION_ERROR)
├── IngestionException
│   ├── FileSourceException (FILE_SOURCE_ERROR)
│   ├── UnsupportedFileTypeException (UNSUPPORTED_FILE_TYPE)
│   └── FileTooLargeException (FILE_TOO_LARGE)
├── PreProcessingException
│   ├── PageExtractionException (PAGE_EXTRACTION_ERROR)
│   └── QualityTooLowException (QUALITY_TOO_LOW)
├── SplittingException (SPLITTING_ERROR)
├── ClassificationException
│   └── ClassificationConfidenceTooLowException (CLASSIFICATION_CONFIDENCE_LOW)
├── ExtractionException (EXTRACTION_ERROR)
├── DocumentValidationException (VALIDATION_ERROR)
├── PipelineException (PIPELINE_EXECUTION_ERROR)
├── JobNotFoundException (JOB_NOT_FOUND)
└── StorageException (STORAGE_ERROR)
```

pyfly's error handling middleware maps these exceptions to HTTP responses using the `code` field, producing a standard error JSON body with `status`, `error`, `message`, `code`, and `timestamp`.

## Observability

### Domain Events

Pydantic-based events are published at key processing milestones. All events extend `IntelliDocEvent` and carry `event_type`, `timestamp`, `correlation_id`, and `tenant_id`.

| Event Type | Published When |
|------------|---------------|
| `intellidoc.job.created` | A new processing job is submitted |
| `intellidoc.job.started` | Pipeline execution begins |
| `intellidoc.job.completed` | Job finishes (success or partial success) |
| `intellidoc.job.failed` | Job fails entirely |
| `intellidoc.document.classified` | A single document is classified |
| `intellidoc.document.extracted` | Extraction completes for a document |
| `intellidoc.document.validated` | Validation completes for a document |
| `intellidoc.document.processed` | A single document is fully processed and persisted |

Events include contextual data: job ID, document index, confidence scores, token usage, field counts, and validation results. They can be consumed by listeners for audit logging, real-time dashboards, or integration triggers.

### Metrics

`MetricsCollector` records in-memory counters and gauges using Prometheus-compatible naming. When pyfly's observability module is available, these are bridged to Prometheus exporters.

**Job-level metrics:**
- `intellidoc_jobs_total{status}` — Total jobs by final status
- `intellidoc_jobs_duration_milliseconds` — End-to-end processing time
- `intellidoc_jobs_active` — Currently running jobs (gauge)

**Document-level metrics:**
- `intellidoc_documents_processed_total` — Documents processed
- `intellidoc_documents_classified_total` — Documents classified
- `intellidoc_documents_extracted_total` — Documents with successful extraction
- `intellidoc_documents_validated_total` — Documents validated

**Resource metrics:**
- `intellidoc_pages_processed_total` — Total pages processed
- `intellidoc_fields_extracted_total` — Total fields extracted
- `intellidoc_tokens_used_total` — Total LLM tokens consumed
- `intellidoc_cost_usd_total` — Estimated cost in USD

**Per-stage duration metrics:**
- `intellidoc_ingestion_duration_milliseconds`
- `intellidoc_preprocessing_duration_milliseconds`
- `intellidoc_splitting_duration_milliseconds`
- `intellidoc_classification_duration_milliseconds`
- `intellidoc_extraction_duration_milliseconds`
- `intellidoc_validation_duration_milliseconds`

**Error metrics:**
- `intellidoc_errors_total{error_type, stage}` — Errors by type and stage

### Webhooks

`WebhookService` sends HTTP callbacks when jobs complete or fail. Webhook URLs are configured per-job via request tags or globally.

**Payload format (job completed):**
```json
{
  "event": "job.completed",
  "job_id": "abc-123-...",
  "status": "completed"
}
```

**Payload format (job failed):**
```json
{
  "event": "job.failed",
  "job_id": "abc-123-...",
  "error": "Pipeline failed: ..."
}
```

**Security:** When a webhook secret is configured, the payload is signed with HMAC-SHA256. The signature is included in the `X-IntelliDoc-Signature` header as `sha256={hex_digest}`. Consumers should verify this signature before processing the payload.

**Delivery:** Webhooks are delivered with up to 3 retries. The User-Agent is `FireflyIntelliDoc-Webhook/1.0`. HTTP status codes below 300 are considered successful.

## Multi-Tenancy

IntelliDoc supports multi-tenancy through the `tenant_id` field:

- **ProcessRequest** accepts an optional `tenant_id` that propagates through the entire pipeline
- **ProcessingJob** stores the tenant_id for filtering
- **Domain events** carry tenant_id for tenant-aware event routing
- **Analytics** can be filtered by tenant via the jobs listing endpoint
- **Job listing** supports `tenant_id` query parameter for tenant isolation

The catalog (document types, fields, validators) is shared across tenants. Tenant isolation applies at the processing/results level. For full catalog isolation, deploy separate IntelliDoc instances per tenant.
