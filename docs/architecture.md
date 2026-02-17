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

REST controllers expose the framework's capabilities as HTTP endpoints. Each controller
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
- `FormatValidator` — Email, phone, IBAN, regex patterns
- `CrossFieldValidator` — Field matching, sum verification, date ordering
- `VisualValidator` — VLM-based visual checks (signatures, stamps, etc.)
- `BusinessRuleValidator` — Expression evaluation
- `CompletenessValidator` — Required fields, minimum pages

### Layer 6: Auto-Configuration

pyfly's `@configuration` classes with `@conditional_on_property` conditions
wire everything together based on the application's configuration.

- `IntelliDocAutoConfiguration` — Master config, splitters, validators, metrics
- `IngestionAutoConfiguration` — Conditional ingestion adapters
- `StorageAutoConfiguration` — Storage provider selection

Auto-configurations are registered via Python entry points:
```toml
[project.entry-points."pyfly.auto_configuration"]
intellidoc = "fireflyframework_intellidoc.auto_configuration:IntelliDocAutoConfiguration"
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
