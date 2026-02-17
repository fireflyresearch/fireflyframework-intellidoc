<p align="center">
  <img src="images/logo.png" alt="IntelliDoc" width="420">
</p>

<p align="center">
  <strong>Documentation Index</strong>
</p>

---

## Quick Navigation

| If you want to... | Read |
|---|---|
| Understand the architecture and design decisions | [Architecture Guide](architecture.md) |
| Set up a working IDP service from scratch | [Getting Started](getting-started.md) |
| Process documents from the command line | [CLI Reference](cli.md) |
| Look up a specific REST API endpoint | [API Reference](api-reference.md) |
| Tune configuration properties | [Configuration Reference](configuration.md) |
| See real-world document type setups | [Examples](examples.md) |
| Deploy to production | [Deploy Guide](deploy.md) |
| Review what changed between versions | [Changelog](../CHANGELOG.md) |

---

## Conceptual Overview

fireflyframework-intellidoc is a catalog-driven Intelligent Document Processing (IDP) framework.
Instead of hard-coding document types and extraction logic, everything is defined at runtime
through a REST catalog and assembled dynamically by the pipeline.

### Core Concepts

**Document Types** define _what_ the system can process. Each type describes a category of
document (e.g., "Invoice", "Passport", "Lab Report") with visual descriptions, classification
cues, and keywords that guide the Vision-Language Model during classification.

**Catalog Fields** define _what data_ to extract. Fields are reusable definitions stored in a
shared catalog — the same `vendor_name` field can be referenced by invoices, purchase orders,
and credit notes. Each field specifies its type, format constraints, location hints, and can
carry embedded validation rules.

**Validators** define _how_ to verify extracted data. Validators range from simple format checks
(email, IBAN) to cross-field logic (total = subtotal + tax) to VLM-powered visual checks
(is a signature present?). They can be attached to document types or embedded directly in fields.

**Target Schema** controls _which_ fields to extract for a given request. Users can pass explicit
field codes in the `ProcessRequest`, or the system falls back to the document type's default
fields. This makes extraction fully runtime-configurable without code changes.

### How It Works

```
                         ┌──────────────────┐
  Document (PDF/image) → │  Processing      │ → Structured JSON
  + target_schema        │  Pipeline        │   with confidence
  (optional)             └──────────────────┘   scores
```

1. A document is **ingested** from a local file, URL, or cloud storage
2. Pages are **preprocessed** — extracted from PDFs, rotated, enhanced, quality-scored
3. Multi-page files are **split** into individual documents (page-based or VLM-powered)
4. Each document is **classified** against the catalog of known document types
5. **Target fields are resolved** — from the request's `target_schema`, or from the classified document type's defaults
6. Fields are **extracted** by a VLM using a prompt built from the resolved `CatalogField` definitions
7. Extracted data is **validated** against document-type validators and field-level rules
8. Results are **persisted** with full audit trail, confidence scores, and validation outcomes

### The VLM-First Approach

Traditional IDP relies on OCR to convert document images to text, then applies rules or ML
models to the text. This breaks down with handwritten content, complex layouts, poor scans,
and visual elements like stamps or signatures.

IntelliDoc sends document page images directly to Vision-Language Models. The VLM understands
layout, reads text in context, and can answer questions about visual elements — all in a single
pass. The catalog provides the VLM with structured context about what to look for and how to
interpret it.

**What flows into the VLM prompt:**

| CatalogField property | Prompt output | Purpose |
|---|---|---|
| `code` + `field_type` | `- invoice_number (text): Invoice Number` | Tells the VLM what to extract |
| `description` | `Description: The unique invoice identifier` | Adds semantic context |
| `required` | `Required: yes` | Signals importance |
| `location_hint` | `Location: Usually near the top of the document` | Spatial guidance |
| `format_pattern` | `Format: YYYY-MM-DD` | Expected format |
| `allowed_values` | `Allowed values: USD, EUR, GBP` | Constrains output |
| `min_value` / `max_value` | `Range: 0.0 to 100.0` | Numeric bounds |
| `table_columns` | Nested column descriptions (recursive) | Defines table structure |

Properties like `tags`, `validation_rules`, and `default_value` are metadata — they don't appear
in the VLM prompt but are used by the validation engine and extraction service respectively.

### Field Resolution Priority

When a processing request arrives, the system resolves which fields to extract in this order:

1. **Explicit `target_schema.field_codes`** from the request — highest priority
2. **Document type `default_field_codes`** — used as fallback after classification identifies the type
3. **Empty** — if neither is available, extraction is skipped

This design means the same document type can be processed differently depending on context:
a quick scan might extract only `invoice_number` and `total_amount`, while a full audit
extracts all 10 default fields.

### Validation Architecture

Validation happens at two levels:

**Document-type validators** are standalone `ValidatorDefinition` entries in the catalog, assigned
to document types. They handle complex checks like cross-field consistency (total = subtotal + tax),
visual verification (signature present), and business rules (discount < 30% of subtotal).

**Field-level validation rules** are `FieldValidationRule` entries embedded directly in `CatalogField`
definitions. They handle simple per-field checks (format, range, required) that logically belong
with the field definition. At validation time, these are converted to ephemeral `ValidatorDefinition`
objects and run through the same `ValidationEngine`.

The `ValidationEngine` dispatches each validator to the appropriate handler based on its type.
If a handler fails with an exception, the engine captures it as a failed `ValidationResult`
and continues — it never raises, ensuring all validators run regardless of individual failures.

| Validator Type | Handler | Typical Use |
|---|---|---|
| `format` | `FormatValidator` | Email, phone, IBAN, regex, date format |
| `range` | `FormatValidator` | Numeric min/max bounds |
| `required` | `CompletenessValidator` | Field presence and non-emptiness |
| `cross_field` | `CrossFieldValidator` | Sum verification, field matching, date ordering |
| `visual` | `VisualValidator` | VLM-based checks — signature, stamp, photo, watermark |
| `business_rule` | `BusinessRuleValidator` | Expression evaluation against extracted data |
| `completeness` | `CompletenessValidator` | Required fields present, minimum page count |
| `checksum` | `FormatValidator` | IBAN MOD97, Luhn algorithm |
| `lookup` | `BusinessRuleValidator` | Value lookup against reference datasets |

---

## Documentation Guide

### [Architecture Guide](architecture.md)

Deep dive into the framework's design — the six architectural layers, all port interfaces,
adapter implementations, the processing pipeline with flow diagrams, data flow through the
system, error handling hierarchy, observability (events, metrics, webhooks), and multi-tenancy.

**Key sections:**
- Design Philosophy (VLM-first, catalog-driven, hexagonal)
- Layered Architecture (exposure → services → domain → ports → adapters → auto-config)
- Processing Pipeline (7-step flow with per-document fan-out)
- Data Flow (visual diagram from request to result)
- Fields Catalog (reusability, embedded validation, runtime override)
- Integration Points (pyfly DI, fireflyframework-genai agents)
- Extensibility (adding sources, validators, splitters, document types)
- Error Handling (exception hierarchy with codes)
- Observability (8 domain events, 18 metrics, webhooks with HMAC)
- Multi-Tenancy

### [Getting Started](getting-started.md)

Step-by-step tutorial to build an invoice processing service from zero.

**Covers:** Install → Create app → Configure → Start → Create document type → Define catalog
fields → Assign default fields → Create validators → Assign validators → Process sync/async →
Target schema override → Batch processing → Export results → Analytics

### [CLI Reference](cli.md)

Complete documentation for the `intellidoc` command-line tool.

**Covers:** process (single file) → batch (directory) → catalog validate → catalog show →
API key resolution → catalog YAML format → output formats (JSON, table, CSV) →
CI/CD integration → CLI vs REST API comparison

### [API Reference](api-reference.md)

Complete documentation of all 43 REST endpoints across 9 controllers.

**Sections:**
1. Document Type Management (9 endpoints)
2. Fields Catalog (6 endpoints)
3. Validator Management (7 endpoints)
4. Document Processing (3 endpoints)
5. Job Tracking (4 endpoints)
6. Result Retrieval (5 endpoints — including export)
7. Analytics (5 endpoints)
8. Health & Monitoring (4 endpoints)
9. Response Models, Enumerations, Error Codes

### [Configuration Reference](configuration.md)

All 60+ configuration properties organized by category, with types, defaults, and descriptions.

**Categories:** General, AI Models (per-stage overrides), Processing Pipeline, Timeouts, Retries,
Pre-processing, Classification, Extraction, Storage (local/S3/Azure/GCS), Ingestion Sources,
Cloud credentials, Temp files, Observability, Async processing, MIME types, Webhooks, Multi-tenancy

**Includes:** Example configurations for development, production (AWS), production (Azure), and
multi-model setups.

### [Examples](examples.md)

10 complete real-world examples covering the full spectrum of IDP use cases.

| # | Example | Concepts Demonstrated |
|---|---|---|
| 1 | Invoice Processing | Document type, fields, validators, full setup |
| 2 | Passport | Identity documents, visual validators, MRZ extraction |
| 3 | Driver's License | Compact document types with visual cues |
| 4 | Lab Report | Medical documents, table extraction with enum columns |
| 5 | Lease Agreement | Multi-page legal documents, signature validation |
| 6 | Custom Validators | Email, IBAN, regex, visual stamp, business rules |
| 7 | Visual Splitting | Multi-document PDFs, VLM boundary detection |
| 8 | Expected Type | Skip classification for known document sources |
| 9 | Expected Nature | Narrow classification to a document category |
| 10 | Inline Fields | Ad-hoc extraction with `target_schema.inline_fields` |
| 11 | Field-Level Validation | Embedded `FieldValidationRule` on catalog fields |

### [Changelog](../CHANGELOG.md)

Version history following [Keep a Changelog](https://keepachangelog.com/) with
[Calendar Versioning](https://calver.org/) (YY.MM.PATCH).

---

## Framework Stack

```
┌─────────────────────────────────────────┐
│  fireflyframework-intellidoc            │  ← This framework
│  Catalog-driven IDP with VLM agents     │
├─────────────────────────────────────────┤
│  fireflyframework-genai                 │  ← GenAI metaframework
│  Agents, structured output, pipelines   │
├─────────────────────────────────────────┤
│  pyfly                                  │  ← Application framework
│  DI, web, data, security, config        │
└─────────────────────────────────────────┘
```

- **pyfly** provides the Spring Boot-like foundation: dependency injection, web server,
  data access, security, and YAML configuration with `@config_properties` binding.
- **fireflyframework-genai** provides the AI layer: `FireflyAgent` wrapping Pydantic AI,
  structured output schemas, reasoning strategies, and agent middleware.
- **fireflyframework-intellidoc** builds on both to provide the complete IDP solution:
  catalog management, processing pipeline, validation engine, and operational APIs.

---

## Requirements

- Python >= 3.13
- pyfly >= 0.1.0
- fireflyframework-genai >= 26.02.06
- A VLM-capable API key (OpenAI, Anthropic, or Google)

## License

Apache License 2.0 — Copyright 2026 Firefly Software Solutions Inc
