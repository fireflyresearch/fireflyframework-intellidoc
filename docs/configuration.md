# Configuration Reference

**fireflyframework-intellidoc — All Configuration Properties**

> Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0

---

All properties use the `pyfly.intellidoc.*` prefix in YAML configuration
or `PYFLY_INTELLIDOC_*` prefix as environment variables (uppercased, dots
replaced with underscores).

## General

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable IntelliDoc auto-configuration |
| `api_prefix` | string | `/api/v1/intellidoc` | REST API path prefix |

## AI Models

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `default_model` | string | `openai:gpt-4o` | Default VLM model for all stages |
| `classification_model` | string | `""` | Override model for classification (falls back to default) |
| `extraction_model` | string | `""` | Override model for extraction |
| `splitting_model` | string | `""` | Override model for visual splitting |
| `validation_model` | string | `""` | Override model for visual validation |
| `default_temperature` | float | `0.1` | LLM temperature for all stages |

**Model format:** `provider:model_name` (e.g., `openai:gpt-4o`, `anthropic:claude-sonnet-4-5-20250929`, `google:gemini-2.0-flash`)

**Per-stage override:** If a stage-specific model is set (e.g., `classification_model`), it takes
precedence over `default_model` for that stage. An empty string falls back to the default.

```yaml
pyfly:
  intellidoc:
    default_model: "openai:gpt-4o"
    classification_model: "anthropic:claude-sonnet-4-5-20250929"  # Use Claude for classification
    extraction_model: ""                            # Falls back to gpt-4o
```

## Processing Pipeline

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `max_pages_per_file` | int | `500` | Maximum pages per file |
| `max_file_size_mb` | int | `100` | Maximum file size in MB |
| `default_splitting_strategy` | string | `whole_document` | Default splitting strategy: `whole_document`, `page_based`, `visual` |
| `default_dpi` | int | `300` | DPI for PDF→image conversion |
| `parallel_documents` | int | `5` | Max parallel document processing |

## Timeouts (Seconds)

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ingestion_timeout` | int | `60` | File fetching timeout |
| `preprocessing_timeout` | int | `120` | Preprocessing timeout |
| `splitting_timeout` | int | `60` | Splitting timeout |
| `classification_timeout` | int | `30` | Classification timeout |
| `extraction_timeout` | int | `60` | Extraction timeout |
| `validation_timeout` | int | `30` | Validation timeout |

## Retries

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ingestion_retries` | int | `2` | Ingestion retry count |
| `splitting_retries` | int | `1` | Splitting retry count |
| `classification_retries` | int | `2` | Classification retry count |
| `extraction_retries` | int | `2` | Extraction retry count |

## Pre-processing

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `auto_rotate` | bool | `true` | Auto-detect and correct rotation |
| `auto_enhance` | bool | `true` | Auto-enhance image quality |
| `auto_denoise` | bool | `true` | Auto-denoise images |
| `quality_threshold` | float | `0.3` | Minimum quality score (0.0-1.0). Pages below this threshold trigger a warning. |

## Classification

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `default_confidence_threshold` | float | `0.7` | Minimum classification confidence for resolving catalog default fields. When confidence falls below this threshold, catalog default fields are not used (inline fields and explicit field codes are unaffected). |
| `max_classification_candidates` | int | `5` | Maximum classification candidates returned |

## Extraction

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `extraction_strategy` | string | `single_pass` | Extraction strategy |
| `extraction_pages_per_batch` | int | `5` | Pages per comprehension batch in multi-pass extraction |
| `extraction_single_pass_threshold` | int | `10` | Page count threshold — documents with this many pages or fewer use single-pass extraction; above this threshold, multi-pass memory-driven extraction is used |
| `max_extraction_retries` | int | `2` | Retry count for extraction failures |

## Storage

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `storage_provider` | string | `local` | Storage provider: `local`, `s3`, `azure_blob`, `gcs` |
| `storage_local_path` | string | `/var/intellidoc/storage` | Local storage directory |
| `storage_bucket` | string | `""` | S3/GCS bucket name |
| `storage_container` | string | `""` | Azure blob container name |
| `storage_prefix` | string | `intellidoc/` | Object key prefix |
| `store_original_files` | bool | `true` | Keep original uploaded files |
| `store_page_images` | bool | `true` | Keep extracted page images |
| `store_enhanced_images` | bool | `false` | Keep enhanced (post-processing) images |

## Ingestion Sources

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ingestion_local_enabled` | bool | `true` | Enable local filesystem ingestion |
| `ingestion_url_enabled` | bool | `true` | Enable URL ingestion |
| `ingestion_s3_enabled` | bool | `false` | Enable S3 ingestion |
| `ingestion_azure_enabled` | bool | `false` | Enable Azure Blob ingestion |
| `ingestion_gcs_enabled` | bool | `false` | Enable GCS ingestion |

## S3 Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `s3_region` | string | `""` | AWS region |
| `s3_access_key` | string | `""` | AWS access key ID |
| `s3_secret_key` | string | `""` | AWS secret access key |
| `s3_endpoint_url` | string | `""` | Custom S3 endpoint (for MinIO, LocalStack) |

**Security note:** Use environment variables for credentials:
```bash
export PYFLY_INTELLIDOC_S3_ACCESS_KEY="AKIA..."
export PYFLY_INTELLIDOC_S3_SECRET_KEY="..."
```

## Azure Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `azure_connection_string` | string | `""` | Azure Storage connection string |
| `azure_account_url` | string | `""` | Azure account URL (for managed identity) |

## GCS Configuration

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `gcs_project_id` | string | `""` | Google Cloud project ID |
| `gcs_credentials_path` | string | `""` | Path to service account JSON |

## Temp Files

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `temp_dir` | string | `/tmp/intellidoc` | Temporary directory for processing |
| `cleanup_temp_after_processing` | bool | `true` | Delete temp files after job completes |

## Observability

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `metrics_enabled` | bool | `true` | Enable metrics collection |
| `tracing_enabled` | bool | `true` | Enable distributed tracing |
| `cost_tracking_enabled` | bool | `true` | Track token usage and costs |

## Async Processing

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `async_processing_enabled` | bool | `true` | Enable async processing mode |
| `job_expiry_hours` | int | `168` | Hours before completed jobs are eligible for cleanup (7 days) |

## Supported MIME Types

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `supported_mime_types` | string[] | See below | List of accepted MIME types |

Default supported types:
- `application/pdf`
- `image/png`
- `image/jpeg`
- `image/tiff`
- `image/bmp`
- `image/webp`
- `image/gif`

## Webhooks

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `webhook_enabled` | bool | `false` | Enable webhook notifications on job completion |
| `webhook_default_url` | string | `""` | Default webhook URL (used when not specified per-job) |
| `webhook_secret` | string | `""` | HMAC-SHA256 signing secret for webhook payloads |
| `webhook_retry_count` | int | `3` | Number of delivery attempts per webhook |
| `webhook_timeout_seconds` | int | `30` | HTTP timeout for webhook delivery |

**Per-job webhooks:** Set `webhook_url` and optionally `webhook_secret` in the processing request tags to override the global defaults for a specific job.

**Security note:** Use environment variables for the webhook secret:
```bash
export PYFLY_INTELLIDOC_WEBHOOK_SECRET="your-shared-secret"
```

The webhook payload is signed with HMAC-SHA256 when a secret is configured. Verify the `X-IntelliDoc-Signature` header (`sha256={hex_digest}`) against the raw request body.

## Multi-Tenancy

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `multi_tenancy_enabled` | bool | `false` | Enable multi-tenancy features |

When enabled, the `tenant_id` field on `ProcessRequest` is propagated through the entire pipeline. Jobs and results can be filtered by tenant. The catalog (document types, fields, validators) is shared across tenants.

## CLI Configuration

When using the `intellidoc` CLI, command-line flags override configuration file values.
The CLI also resolves API keys automatically from flags, environment variables, or `.env` files.

### Flag → Config Mapping

| CLI Flag | Config Property | Description |
|----------|----------------|-------------|
| `--model` | `default_model` | VLM model for all stages |
| `--api-key` | N/A | Set via env var (see below) |
| `--splitting-strategy` | `default_splitting_strategy` | `whole_document`, `page_based`, or `visual` |
| `--fields` | N/A | Catalog field codes to extract |
| `--schema` | N/A | Inline extraction schema (`name:type,...` or `@file.json`) |
| `--document-types` | N/A | Ad-hoc types for classification (`code:desc,...` or `@file.json`) |
| `--expected-type` | N/A | Binary classification hint |
| `--parallel` | `parallel_documents` | Batch parallelism |

### API Key Resolution Order

1. `--api-key` flag (highest priority)
2. Environment variable: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`
3. `.env` file in the current directory

### CLI-Specific YAML

The CLI requires `pyfly.shell.enabled: true` in `pyfly.yaml`:

```yaml
pyfly:
  shell:
    enabled: true

  intellidoc:
    enabled: true
    default_model: "openai:gpt-4o"
```

If no `pyfly.yaml` is present, the CLI uses built-in defaults. The `--model` flag
always overrides the config file.

### Catalog YAML

In CLI mode, document types, fields, and validators are loaded from `catalog.yaml`
in the current directory. See the [CLI Reference](cli.md#catalog-yaml-format) for
the full format.

## Example Configurations

### Development (Minimal)

```yaml
pyfly:
  intellidoc:
    enabled: true
    default_model: "openai:gpt-4o"
    storage_provider: "local"
    storage_local_path: "./data/storage"
    temp_dir: "./data/temp"
    default_splitting_strategy: "whole_document"
```

### Production (AWS)

```yaml
pyfly:
  intellidoc:
    enabled: true
    default_model: "anthropic:claude-sonnet-4-5-20250929"
    classification_model: "openai:gpt-4o"

    storage_provider: "s3"
    storage_bucket: "my-company-intellidoc"
    storage_prefix: "processed/"
    store_original_files: true
    store_page_images: false

    ingestion_local_enabled: false
    ingestion_url_enabled: true
    ingestion_s3_enabled: true
    s3_region: "us-east-1"

    max_file_size_mb: 200
    max_pages_per_file: 1000
    default_splitting_strategy: "visual"
    parallel_documents: 10

    default_confidence_threshold: 0.8

    async_processing_enabled: true
    job_expiry_hours: 720  # 30 days

    metrics_enabled: true
    tracing_enabled: true
    cost_tracking_enabled: true
```

### Production (Azure)

```yaml
pyfly:
  intellidoc:
    enabled: true
    default_model: "openai:gpt-4o"

    storage_provider: "azure_blob"
    storage_container: "intellidoc-processed"

    ingestion_azure_enabled: true
    azure_account_url: "https://myaccount.blob.core.windows.net"

    async_processing_enabled: true
```

### Multi-Model Setup

```yaml
pyfly:
  intellidoc:
    enabled: true

    # Fast model for classification (less complex task)
    classification_model: "openai:gpt-4o-mini"

    # Powerful model for extraction (needs high accuracy)
    extraction_model: "anthropic:claude-sonnet-4-5-20250929"

    # Fast model for splitting (visual analysis)
    splitting_model: "openai:gpt-4o-mini"

    # Powerful model for visual validation
    validation_model: "openai:gpt-4o"

    default_temperature: 0.05  # Very deterministic
```
