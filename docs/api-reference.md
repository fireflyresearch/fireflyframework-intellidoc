# API Reference

**fireflyframework-intellidoc — Complete REST API Documentation**

> Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0

---

Base URL: `/api/v1/intellidoc`

All request and response bodies use JSON (`application/json`).

---

## 1. Document Type Management

**Base path:** `/api/v1/intellidoc/document-types`

### POST `/document-types`
Create a new document type in the catalog.

**Status:** `201 Created`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Unique code (`^[a-z][a-z0-9_]*$`, 2-100 chars) |
| `name` | string | Yes | Display name (2-200 chars) |
| `description` | string | Yes | Description (10-2000 chars) |
| `nature` | DocumentNature | Yes | Category: `identity`, `financial`, `legal`, `medical`, `government`, `educational`, `commercial`, `insurance`, `real_estate`, `hr`, `correspondence`, `technical`, `other` |
| `visual_description` | string | No | How the document looks visually (for VLM classification) |
| `visual_cues` | string[] | No | Visual elements to look for |
| `sample_keywords` | string[] | No | Keywords commonly found in this document type |
| `classification_instructions` | string | No | Additional classification guidance for the VLM |
| `classification_confidence_threshold` | float | No | Min confidence (0.0-1.0, default: 0.7) |
| `extraction_instructions` | string | No | Additional extraction guidance |
| `default_field_codes` | string[] | No | Default field codes for extraction |
| `tags` | string[] | No | Freeform tags |
| `supported_languages` | string[] | No | Language codes (default: `["en"]`) |

**Response:** `DocumentTypeResponse`

---

### GET `/document-types`
List document types with filtering and pagination.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `nature` | DocumentNature | - | Filter by nature |
| `active_only` | boolean | `true` | Only return active types |
| `search` | string | - | Search in name/code/description |
| `page` | int | `0` | Page number (zero-based) |
| `size` | int | `20` | Page size |

**Response:** `PageResponse<DocumentTypeResponse>`

---

### GET `/document-types/{document_type_id}`
Get a single document type by ID.

**Response:** `DocumentTypeResponse`

---

### PUT `/document-types/{document_type_id}`
Update a document type. Only provided fields are updated.

**Request Body:** `UpdateDocumentTypeRequest` (all fields optional, includes `default_field_codes`)

**Response:** `DocumentTypeResponse`

---

### DELETE `/document-types/{document_type_id}`
Delete a document type.

**Status:** `204 No Content`

---

### PATCH `/document-types/{document_type_id}/status`
Toggle active/inactive status.

**Request Body:**
```json
{ "is_active": true }
```

**Response:** `DocumentTypeResponse`

---

### PUT `/document-types/{document_type_id}/default-fields`
Set the default field codes for a document type.

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `field_codes` | string[] | Yes | List of catalog field codes |

**Response:** `DocumentTypeResponse`

---

### GET `/document-types/natures`
List all document natures with counts.

**Response:** `NatureResponse[]`

---

### POST `/document-types/{document_type_id}/validators`
Assign validators to a document type.

**Request Body:**
```json
{ "validator_ids": ["uuid-1", "uuid-2"] }
```

**Response:** `DocumentTypeResponse`

---

## 1b. Fields Catalog

**Base path:** `/api/v1/intellidoc/fields`

### POST `/fields`
Create a new field in the catalog.

**Status:** `201 Created`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Unique code (`^[a-z][a-z0-9_]*$`, 2-100 chars) |
| `display_name` | string | Yes | Human-readable name (1-200 chars) |
| `field_type` | FieldType | Yes | `text`, `number`, `date`, `currency`, `boolean`, `email`, `phone`, `address`, `table`, `list`, `enum`, `image_region` |
| `description` | string | No | Field description (guides extraction) |
| `required` | boolean | No | Whether the field is required |
| `default_value` | any | No | Default if not extracted |
| `format_pattern` | string | No | Expected format (e.g., `YYYY-MM-DD`) |
| `min_value` | float | No | Minimum numeric value |
| `max_value` | float | No | Maximum numeric value |
| `allowed_values` | string[] | No | Enum constraint |
| `table_columns` | CreateFieldRequest[] | No | Column definitions (for `table` type) |
| `location_hint` | string | No | Where to look on the document |
| `validation_rules` | FieldValidationRuleRequest[] | No | Embedded validation rules |
| `tags` | string[] | No | Freeform tags |

**FieldValidationRuleRequest:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rule_type` | ValidatorType | Yes | `format`, `range`, `required`, etc. |
| `severity` | ValidatorSeverity | No | `error` (default), `warning`, `info` |
| `config` | object | No | Type-specific configuration |
| `message` | string | No | Custom error message |

**Response:** `CatalogFieldResponse`

---

### GET `/fields`
List fields with filtering and pagination.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `field_type` | FieldType | - | Filter by field type |
| `active_only` | boolean | `true` | Only return active fields |
| `search` | string | - | Search in code/display_name/description |
| `page` | int | `0` | Page number (zero-based) |
| `size` | int | `20` | Page size |

**Response:** `PageResponse<CatalogFieldResponse>`

---

### GET `/fields/{field_id}`
Get a single field by ID.

**Response:** `CatalogFieldResponse`

---

### GET `/fields/by-code/{code}`
Get a single field by its unique code.

**Response:** `CatalogFieldResponse`

---

### PUT `/fields/{field_id}`
Update a field. Only provided fields are updated.

**Request Body:** `UpdateFieldRequest` (all fields optional)

**Response:** `CatalogFieldResponse`

---

### DELETE `/fields/{field_id}`
Delete a field.

**Status:** `204 No Content`

---

## 2. Validator Management

**Base path:** `/api/v1/intellidoc/validators`

### POST `/validators`
Create a new validator.

**Status:** `201 Created`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | Unique code |
| `name` | string | Yes | Display name |
| `description` | string | Yes | Description |
| `validator_type` | ValidatorType | Yes | `format`, `range`, `required`, `cross_field`, `visual`, `business_rule`, `completeness`, `checksum`, `lookup` |
| `severity` | ValidatorSeverity | No | `error` (default), `warning`, `info` |
| `config` | object | No | Type-specific configuration |
| `applicable_natures` | DocumentNature[] | No | Limit to specific natures |
| `applicable_document_types` | UUID[] | No | Limit to specific types |
| `applicable_fields` | string[] | No | Limit to specific fields |
| `visual_prompt` | string | No | VLM prompt (for `visual` type) |
| `visual_expected` | string | No | Expected visual element description |
| `rule_expression` | string | No | Expression (for `business_rule` type) |

**Response:** `ValidatorResponse`

---

### GET `/validators`
List validators with filtering.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `validator_type` | ValidatorType | - | Filter by type |
| `severity` | ValidatorSeverity | - | Filter by severity |
| `nature` | DocumentNature | - | Filter by applicable nature |
| `active_only` | boolean | `true` | Only active validators |
| `page` | int | `0` | Page number |
| `size` | int | `20` | Page size |

**Response:** `PageResponse<ValidatorResponse>`

---

### GET `/validators/{validator_id}`
Get a single validator.

**Response:** `ValidatorResponse`

---

### PUT `/validators/{validator_id}`
Update a validator.

**Response:** `ValidatorResponse`

---

### DELETE `/validators/{validator_id}`
Delete a validator.

**Status:** `204 No Content`

---

### GET `/validators/types`
List available validator types with configuration schemas.

**Response:** `ValidatorTypeInfo[]`

---

### GET `/validators/by-document-type/{document_type_id}`
List validators assigned to a document type.

**Response:** `ValidatorResponse[]`

---

## 3. Document Processing

**Base path:** `/api/v1/intellidoc/process`

### POST `/process`
Submit a document for processing.

**Status:** `202 Accepted`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_type` | string | Yes | `local`, `url`, `s3`, `azure_blob`, `gcs` |
| `source_reference` | string | Yes | Path, URL, or URI |
| `filename` | string | Yes | Original filename |
| `expected_type` | string | No | Skip classification — use this type |
| `expected_nature` | string | No | Narrow classification to this nature |
| `splitting_strategy` | string | No | Override: `page_based`, `visual` |
| `tenant_id` | string | No | Multi-tenancy identifier |
| `correlation_id` | string | No | External correlation ID |
| `tags` | object | No | Key-value tags |
| `async_mode` | boolean | No | `true` for async (default: `false`) |
| `target_schema` | TargetSchema | No | Override extraction fields (see below) |

**TargetSchema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `field_codes` | string[] | No | Catalog field codes to extract |
| `inline_fields` | InlineFieldDefinition[] | No | Ad-hoc field definitions |
| `extraction_strategy` | string | No | `"single_pass"` (default) |

**InlineFieldDefinition** (for ad-hoc fields not in the catalog):
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Internal field name |
| `display_name` | string | Yes | Human-readable name |
| `field_type` | FieldType | Yes | `text`, `number`, `date`, `currency`, `boolean`, `email`, `phone`, `address`, `table`, `list`, `enum`, `image_region` |
| `description` | string | No | Description to guide extraction |
| `required` | boolean | No | Whether the field is required |
| `location_hint` | string | No | Where to look on the document |

**Response (sync):**
```json
{
  "job_id": "...",
  "status": "completed",
  "message": "Processing completed.",
  "result": { /* ProcessingResultResponse */ }
}
```

**Response (async):**
```json
{
  "job_id": "...",
  "status": "pending",
  "message": "Processing job accepted. Poll for status."
}
```

---

### POST `/process/batch`
Submit multiple documents for async processing.

**Status:** `202 Accepted`

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `items` | ProcessRequest[] | Yes | 1-100 documents |
| `stop_on_failure` | boolean | No | Stop on first submission failure |

**Response:** `BatchProcessResponse`

---

### GET `/process/supported-sources`
List enabled ingestion sources.

**Response:** `SourceInfo[]`

---

## 4. Job Tracking

**Base path:** `/api/v1/intellidoc/jobs`

### GET `/jobs`
List processing jobs with filtering.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | JobStatus | - | Filter by status |
| `tenant_id` | string | - | Filter by tenant |
| `from_date` | datetime | - | Created after |
| `to_date` | datetime | - | Created before |
| `page` | int | `0` | Page number |
| `size` | int | `20` | Page size |

**JobStatus values:** `pending`, `ingesting`, `preprocessing`, `splitting`, `classifying`, `extracting`, `validating`, `completed`, `failed`, `partially_completed`, `cancelled`

**Response:** `PageResponse<JobResponse>`

---

### GET `/jobs/{job_id}`
Get full job details.

**Response:** `JobResponse`

---

### GET `/jobs/{job_id}/status`
Lightweight status for polling.

**Response:** `JobStatusResponse`
```json
{
  "job_id": "...",
  "status": "extracting",
  "current_step": "extract",
  "progress_percent": 65.0,
  "documents_processed": 2,
  "documents_succeeded": 2,
  "documents_failed": 0,
  "total_documents_detected": 3
}
```

---

### DELETE `/jobs/{job_id}`
Cancel a pending or in-progress job.

**Status:** `204 No Content`

---

## 5. Result Retrieval

**Base path:** `/api/v1/intellidoc/results`

### GET `/results/{job_id}`
Get complete processing result.

**Response:** `ProcessingResultResponse`

---

### GET `/results/{job_id}/documents/{document_id}`
Get result for a specific document.

**Response:** `DocumentResultResponse`

---

### GET `/results/{job_id}/extracted-data`
Get extracted fields only (for integrations).

**Response:** `ExtractedDataResponse[]`
```json
[
  {
    "document_id": "...",
    "document_type_code": "invoice",
    "page_range": "1-2",
    "fields": { "invoice_number": "INV-001", ... },
    "confidence": { "invoice_number": 0.95, ... },
    "is_valid": true
  }
]
```

---

### GET `/results/{job_id}/export`
Export results in JSON or CSV format.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `format` | string | `json` | `json` or `csv` |

**Response:** `ExportResponse`

---

## 6. Analytics

**Base path:** `/api/v1/intellidoc/analytics`

### GET `/analytics/summary`
Aggregated processing statistics.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `from_date` | datetime | Period start |
| `to_date` | datetime | Period end |

**Response:** `AnalyticsSummaryResponse`

---

### GET `/analytics/by-document-type`
Breakdown by document type.

**Response:** `DocumentTypeAnalytics[]`

---

### GET `/analytics/by-nature`
Breakdown by document nature.

**Response:** `NatureAnalytics[]`

---

### GET `/analytics/validation-failures`
Top validation failures.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | `10` | Max results |
| `from_date` | datetime | - | Period start |
| `to_date` | datetime | - | Period end |

**Response:** `ValidationFailureAnalytics[]`

---

### GET `/analytics/cost`
Cost analysis by time period.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `from_date` | datetime | - | Period start |
| `to_date` | datetime | - | Period end |
| `group_by` | string | `day` | `day`, `week`, `month` |

**Response:** `CostAnalyticsResponse`

---

## 7. Health & Monitoring

**Base path:** `/api/v1/intellidoc/health`

### GET `/health`
Basic health check.

**Response:**
```json
{ "status": "UP", "version": "26.02.01", "timestamp": "..." }
```

---

### GET `/health/ready`
Component readiness check.

**Response:**
```json
{
  "ready": true,
  "components": {
    "config": { "status": "UP", "details": { "enabled": true } },
    "storage": { "status": "UP", "details": { "provider": "local" } },
    "ai_model": { "status": "UP", "details": { "model": "openai:gpt-4o" } }
  }
}
```

---

### GET `/health/config`
Non-sensitive configuration info.

**Response:** `ConfigInfoResponse`

---

### GET `/health/metrics`
Current metric values.

**Response:** `{ "metric_name": value, ... }`

---

## Response Models

### PageResponse\<T\>
```json
{
  "content": [ /* items */ ],
  "page": 0,
  "size": 20,
  "total_elements": 42,
  "total_pages": 3,
  "has_next": true,
  "has_previous": false
}
```

### DocumentConfidence
Values: `high` (>= 0.9), `medium` (>= 0.7), `low` (>= 0.5), `very_low` (< 0.5)

### ValidatorSeverity
Values: `error`, `warning`, `info`

### Error Response
Errors follow pyfly's standard error format:
```json
{
  "status": 404,
  "error": "Not Found",
  "message": "Document type not found: abc-123",
  "code": "DOCUMENT_TYPE_NOT_FOUND",
  "timestamp": "2026-02-17T10:00:00"
}
```

---

## Enumerations Reference

### FieldType
| Value | Description |
|-------|-------------|
| `text` | Free-form text string |
| `number` | Numeric value (integer or decimal) |
| `date` | Calendar date (ISO 8601 preferred) |
| `currency` | Monetary amount |
| `boolean` | True/false value |
| `email` | Email address |
| `phone` | Phone number |
| `address` | Postal/physical address |
| `table` | Tabular data with nested column definitions |
| `list` | Ordered list of values |
| `enum` | Value constrained to `allowed_values` |
| `image_region` | Bounding box or region of interest in the page image |

### ValidatorType
| Value | Handler | Description |
|-------|---------|-------------|
| `format` | `FormatValidator` | Pattern matching — email, phone, IBAN, regex, date format |
| `range` | `FormatValidator` | Numeric range validation (min/max bounds) |
| `required` | `CompletenessValidator` | Field presence and non-emptiness |
| `cross_field` | `CrossFieldValidator` | Multi-field logic — sum verification, field matching, date ordering |
| `visual` | `VisualValidator` | VLM-based visual checks — signatures, stamps, photos, watermarks |
| `business_rule` | `BusinessRuleValidator` | Expression evaluation against extracted data |
| `completeness` | `CompletenessValidator` | Required fields present, minimum page count |
| `checksum` | `FormatValidator` | Algorithmic checksum validation (IBAN MOD97, Luhn, etc.) |
| `lookup` | `BusinessRuleValidator` | Value lookup against reference datasets |

### DocumentNature
Values: `identity`, `financial`, `legal`, `medical`, `government`, `educational`, `commercial`, `insurance`, `real_estate`, `hr`, `correspondence`, `technical`, `other`

### JobStatus
Values: `pending`, `ingesting`, `preprocessing`, `splitting`, `classifying`, `extracting`, `validating`, `completed`, `failed`, `partially_completed`, `cancelled`

### Error Codes

| Code | HTTP Status | Description |
|------|:-----------:|-------------|
| `DOCUMENT_TYPE_NOT_FOUND` | 404 | Document type does not exist |
| `DOCUMENT_TYPE_DUPLICATE` | 409 | Document type code already taken |
| `FIELD_NOT_FOUND` | 404 | Catalog field does not exist |
| `FIELD_DUPLICATE` | 409 | Field code already taken |
| `VALIDATOR_NOT_FOUND` | 404 | Validator does not exist |
| `VALIDATOR_DUPLICATE` | 409 | Validator code already taken |
| `TARGET_SCHEMA_RESOLUTION_ERROR` | 400 | One or more field codes in target_schema could not be resolved |
| `FILE_SOURCE_ERROR` | 502 | Could not fetch file from source |
| `UNSUPPORTED_FILE_TYPE` | 415 | MIME type not in supported list |
| `FILE_TOO_LARGE` | 413 | File exceeds `max_file_size_mb` |
| `PAGE_EXTRACTION_ERROR` | 422 | Could not extract pages from document |
| `QUALITY_TOO_LOW` | 422 | Document quality below threshold |
| `CLASSIFICATION_CONFIDENCE_LOW` | 422 | No classification candidate above threshold |
| `PIPELINE_EXECUTION_ERROR` | 500 | General pipeline failure |
| `JOB_NOT_FOUND` | 404 | Processing job does not exist |
| `STORAGE_ERROR` | 500 | Storage backend failure |
