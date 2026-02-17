# Changelog

All notable changes to fireflyframework-intellidoc will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (YY.MM.PATCH).

## [26.02.02] - 2026-02-17

### Added

#### CLI Tool
- `intellidoc` command-line tool for processing documents without a web server or database
- `intellidoc process` — single document processing with model, fields, and format options
- `intellidoc batch` — directory-based batch processing with parallel execution
- `intellidoc catalog validate` — validate catalog YAML files
- `intellidoc catalog show` — display catalog contents as table or JSON
- In-memory catalog and result storage adapters for CLI mode
- Catalog YAML loader for defining document types, fields, and validators in YAML
- API key resolution from flags, environment variables, and `.env` files
- Rich progress bar and branded banner output
- Output formats: JSON (compact/pretty), table, CSV
- CLI auto-configuration conditional on `pyfly.shell.enabled`

#### Interactive Installer
- `install.sh` — interactive TUI installer with `curl | bash` support
- System prerequisite checks (Python, uv, git)
- Installation profiles: CLI only, Minimal, Standard, Full, Custom
- VLM provider selection and API key setup
- Storage backend configuration (local, S3, Azure, GCS)
- Automatic `pyfly.yaml` and `.env` generation

### Changed

#### Fields Catalog (Breaking Change)
- **Replaced** `ExtractionSchema` and `FieldDefinition` with `CatalogField` — a reusable, self-describing field definition stored in the fields catalog
- **Added** `FieldValidationRule` — embedded validation rules on catalog fields (format, range, required checks travel with the field)
- **Added** `FieldCatalogPort` — new persistence port replacing `ExtractionSchemaCatalogPort`
- **Added** `FieldController` — REST controller at `/api/v1/intellidoc/fields` with 6 CRUD endpoints
- **Added** `TargetSchema` — runtime extraction override via `target_schema` in `ProcessRequest`
- **Replaced** `DocumentType.extraction_schema_id` with `DocumentType.default_field_codes` — document types reference field codes instead of a monolithic schema
- **Added** `PUT /document-types/{id}/default-fields` endpoint for assigning default field codes
- **Removed** `GET/PUT /document-types/{id}/extraction-schema` endpoints
- **Modified** `ExtractionService` — now accepts `list[CatalogField]` instead of looking up `ExtractionSchema` by document type
- **Modified** `ValidationService` — runs field-level validation rules (from `CatalogField.validation_rules`) in addition to document-type validators
- **Modified** `ProcessingOrchestrator` — resolves target fields between classification and extraction (explicit `target_schema` > document type `default_field_codes`)
- **Added** exceptions: `FieldNotFoundException`, `FieldAlreadyExistsException`, `TargetSchemaResolutionException`
- **Removed** `ExtractionSchemaNotFoundException`

## [26.02.01] - 2026-02-17

### Added

#### Catalog Management
- Document type CRUD with visual descriptions, classification cues, and nature taxonomy
- Field catalog management with 12 field types (text, number, date, currency, boolean, email, phone, address, table, list, enum, image_region)
- Validator catalog with 9 validator types (format, range, required, cross_field, visual, business_rule, completeness, checksum, lookup)
- REST API with 9 document type endpoints, 6 field catalog endpoints, and 7 validator endpoints

#### Ingestion
- Multi-source file ingestion: local filesystem, HTTP/HTTPS URLs, Amazon S3, Azure Blob Storage, Google Cloud Storage
- MIME type validation and file size limits
- Conditional adapter registration based on configuration

#### Pre-processing
- PDF to page image conversion via pdf2image
- Automatic rotation detection and correction (EXIF-based)
- Image enhancement pipeline (denoise, contrast, sharpen)
- Per-page quality scoring (brightness, contrast, sharpness)

#### Splitting
- Page-based splitting strategy (each page = one document)
- VLM-powered visual boundary detection for multi-document files

#### Classification
- Catalog-driven VLM classification with dynamic prompt generation
- Confidence thresholds with per-document-type overrides
- Multi-candidate ranking with reasoning

#### Extraction
- Field-driven VLM extraction with structured output
- 12 field types including nested table columns
- Per-field confidence scoring
- Default value support for optional fields

#### Validation
- Format validators (email, phone, IBAN with MOD97, regex patterns)
- Cross-field validators (field matching, sum verification with tolerance, date ordering)
- VLM-powered visual validators (signature, stamp, photo, watermark detection)
- Business rule expression evaluation with safe operators
- Completeness validators (required fields, minimum pages, field percentage)
- Validation engine with automatic dispatch by validator type

#### Pipeline & Orchestration
- 7-step processing pipeline (ingest, preprocess, split, classify, extract, validate, persist)
- Full job lifecycle management with status tracking and progress reporting
- Per-document fan-out with partial completion support
- Synchronous and asynchronous processing modes
- Batch processing with stop-on-failure option

#### Operational APIs
- Processing submission (sync/async/batch) with 3 endpoints
- Job tracking with status polling (4 endpoints)
- Result retrieval with document detail and export (5 endpoints)
- Analytics with summary, by-type, by-nature, validation failures, and cost analysis (5 endpoints)
- Health, readiness, config, and metrics endpoints (4 endpoints)
- Total: 43 REST endpoints across 9 controllers

#### Observability
- 8 domain events (job created/started/completed/failed, document classified/extracted/validated/processed)
- In-memory metrics collector with 18 named metrics
- Webhook callbacks with HMAC-SHA256 signatures and retry logic

#### Infrastructure
- Hexagonal architecture with Protocol-based ports
- Auto-configuration via pyfly entry points
- 60+ configuration properties with environment variable support
- Apache License 2.0
