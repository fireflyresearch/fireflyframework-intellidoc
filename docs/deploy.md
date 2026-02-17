# Deployment Guide

This guide covers deploying fireflyframework-intellidoc to production environments.

---

## Prerequisites

- Python >= 3.13
- A VLM API key (OpenAI, Anthropic, or Google)
- Storage backend (local filesystem, S3, Azure Blob, or GCS)
- Optional: PostgreSQL for persistent result storage

---

## CLI Tool

The `intellidoc` CLI is installed automatically with the package — no extra dependencies
or configuration needed. It processes documents directly from the terminal using the
same engine as the web server.

```bash
pip install fireflyframework-intellidoc
export OPENAI_API_KEY="sk-..."
intellidoc process document.pdf
```

The CLI is ideal for:
- **CI/CD pipelines** — validate catalogs and process documents in automated workflows
- **Developer workstations** — quick document processing without running a server
- **Batch scripting** — process directories of documents with `intellidoc batch`
- **Edge deployments** — lightweight processing without database infrastructure

See the [CLI Reference](cli.md) for full command documentation.

---

## Single-Server Deployment

### Install

Use the interactive installer or install manually:

```bash
# Interactive
curl -fsSL https://raw.githubusercontent.com/fireflyframework/fireflyframework-intellidoc/main/install.sh | bash

# Manual
python3 -m venv .venv && source .venv/bin/activate
pip install "fireflyframework-intellidoc[web,s3,postgresql,observability]"
```

### systemd Service

Create `/etc/systemd/system/intellidoc.service`:

```ini
[Unit]
Description=IntelliDoc IDP Service
After=network.target

[Service]
Type=exec
User=intellidoc
Group=intellidoc
WorkingDirectory=/opt/intellidoc
EnvironmentFile=/opt/intellidoc/.env
ExecStart=/opt/intellidoc/.venv/bin/pyfly run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now intellidoc
```

### Reverse Proxy (Caddy)

```
intellidoc.example.com {
    reverse_proxy localhost:8080
}
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name intellidoc.example.com;

    ssl_certificate     /etc/ssl/certs/intellidoc.pem;
    ssl_certificate_key /etc/ssl/private/intellidoc.key;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

### Environment Variables

Manage secrets via `/opt/intellidoc/.env`:

```bash
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

Set `chmod 600 .env` — the file is read by pyfly at startup.

---

## Docker Deployment

### Dockerfile

```dockerfile
# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

RUN pip install uv

WORKDIR /build
COPY . .
RUN uv venv /app/.venv \
    && uv pip install --python /app/.venv/bin/python \
       "fireflyframework-intellidoc[web,s3,postgresql,observability]"

# ── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.13-slim

# System dependencies for pdf-images / ocr (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyfly.yaml .

EXPOSE 8080
CMD ["pyfly", "run"]
```

### docker-compose.yml

```yaml
services:
  intellidoc:
    build: .
    ports:
      - "8080:8080"
    env_file: .env
    volumes:
      - storage:/app/intellidoc-storage
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: intellidoc
      POSTGRES_USER: intellidoc
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U intellidoc"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  storage:
  pgdata:
```

```bash
docker compose up -d
```

---

## Production Configuration

### pyfly.yaml

```yaml
pyfly:
  app:
    module: fireflyframework_intellidoc.main:app

  server:
    port: 8080
    workers: 4

  intellidoc:
    enabled: true

    # Models — use fast model for classification, accurate for extraction
    default_model: "openai:gpt-4o"
    classification_model: "openai:gpt-4o-mini"
    extraction_model: "openai:gpt-4o"
    visual_validation_model: "openai:gpt-4o"

    # Processing
    max_file_size_mb: 100
    max_pages_per_file: 500
    default_splitting_strategy: "whole_document"  # or "visual" for multi-document files
    default_confidence_threshold: 0.7
    parallel_documents: 4

    # Storage
    storage_provider: "s3"
    storage_s3_bucket: "my-intellidoc-bucket"
    storage_s3_region: "us-east-1"

    # Async processing
    async_processing_enabled: true

    # Webhooks
    webhook_enabled: true
    webhook_hmac_secret: "${WEBHOOK_HMAC_SECRET}"
```

### Model Selection Strategy

| Stage | Recommended Model | Rationale |
|-------|------------------|-----------|
| Classification | `gpt-4o-mini` / `gemini-2.0-flash` | Fast, low-cost — classification needs pattern matching, not deep reasoning |
| Extraction | `gpt-4o` / `claude-sonnet-4-5-20250929` | Accurate structured output for field extraction |
| Visual validation | `gpt-4o` | Needs visual understanding for signature/stamp detection |

### Storage Setup

**Amazon S3:**
```yaml
storage_provider: "s3"
storage_s3_bucket: "intellidoc-docs"
storage_s3_region: "us-east-1"
storage_s3_prefix: "documents/"
```

**Azure Blob Storage:**
```yaml
storage_provider: "azure_blob"
storage_azure_container: "intellidoc-docs"
```

**Google Cloud Storage:**
```yaml
storage_provider: "gcs"
storage_gcs_bucket: "intellidoc-docs"
storage_gcs_project: "my-project"
```

### PostgreSQL Persistence

Install with the `postgresql` extra, then configure:

```yaml
pyfly:
  data:
    relational:
      url: "postgresql+asyncpg://intellidoc:${DB_PASSWORD}@localhost:5432/intellidoc"
```

### Webhooks

IntelliDoc sends webhook callbacks on job completion:

```yaml
pyfly:
  intellidoc:
    webhook_enabled: true
    webhook_url: "https://your-app.example.com/webhook/intellidoc"
    webhook_hmac_secret: "${WEBHOOK_HMAC_SECRET}"
```

Payloads are signed with HMAC-SHA256 in the `X-Webhook-Signature` header.

### Multi-Tenancy

Enable tenant isolation with the `security` extra:

```yaml
pyfly:
  intellidoc:
    multi_tenancy_enabled: true
    tenant_header: "X-Tenant-ID"
```

Each tenant gets isolated document types, fields, validators, and results.

---

## Monitoring & Observability

### Health Endpoint

```bash
curl http://localhost:8080/api/v1/intellidoc/health
```

Returns `200` with component status (VLM connectivity, storage, database).

Use `/api/v1/intellidoc/health/ready` for load balancer readiness probes.

### Prometheus Metrics

Install with the `observability` extra. Metrics are exposed at `/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `intellidoc_documents_processed_total` | Counter | Total documents processed |
| `intellidoc_processing_duration_seconds` | Histogram | End-to-end processing time |
| `intellidoc_classification_confidence` | Histogram | Classification confidence distribution |
| `intellidoc_extraction_fields_total` | Counter | Fields extracted |
| `intellidoc_validation_failures_total` | Counter | Validation failures by type |
| `intellidoc_active_jobs` | Gauge | Currently processing jobs |
| `intellidoc_vlm_requests_total` | Counter | VLM API calls |
| `intellidoc_vlm_cost_total` | Counter | Estimated VLM cost (USD) |

### OpenTelemetry Tracing

```yaml
pyfly:
  observability:
    tracing:
      enabled: true
      exporter: "otlp"
      endpoint: "http://jaeger:4317"
```

Each processing pipeline run creates a trace with spans for every stage (ingest, preprocess, split, classify, extract, validate, persist).

### Log Configuration

```yaml
pyfly:
  logging:
    level: "INFO"
    format: "json"
```

Structured JSON logs include `job_id`, `document_type`, `tenant_id`, and processing stage for filtering.

---

## Scaling

### Horizontal Scaling

IntelliDoc is stateless when using cloud storage and PostgreSQL — run multiple instances behind a load balancer:

```
                    ┌── IntelliDoc (instance 1)
Load Balancer ──────┼── IntelliDoc (instance 2)  ──── PostgreSQL
                    └── IntelliDoc (instance 3)       S3 / Azure / GCS
```

### Parallel Document Processing

Tune `parallel_documents` based on your VLM rate limits and CPU:

```yaml
pyfly:
  intellidoc:
    parallel_documents: 4   # Process 4 documents concurrently per instance
```

### Worker Architecture with Messaging

For high-throughput deployments, decouple submission from processing using Kafka or RabbitMQ:

```yaml
pyfly:
  intellidoc:
    async_processing_enabled: true
    messaging_backend: "kafka"

  messaging:
    kafka:
      bootstrap_servers: "kafka:9092"
      topic: "intellidoc-jobs"
```

```
API Server ──publish──→ Kafka ──consume──→ Worker (N instances)
    │                                           │
    └─── poll status ← PostgreSQL ← persist ────┘
```

---

## Security

### API Authentication

Enable with the `security` extra:

```yaml
pyfly:
  security:
    enabled: true
    jwt:
      issuer: "https://auth.example.com"
      audience: "intellidoc-api"
      jwks_url: "https://auth.example.com/.well-known/jwks.json"
```

Alternatively, use API key authentication:

```yaml
pyfly:
  security:
    enabled: true
    api_keys:
      enabled: true
```

### HTTPS / TLS Termination

Terminate TLS at the reverse proxy (Caddy, Nginx, cloud load balancer). IntelliDoc listens on plain HTTP internally.

### API Key Rotation

When using API key authentication:

1. Generate a new key and add it to the allowed keys list
2. Update clients to use the new key
3. Remove the old key from the allowed list

Zero-downtime rotation — both keys are valid during the transition.

### Webhook HMAC Verification

Verify webhook payloads using HMAC-SHA256:

```python
import hmac, hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Requirements

- Python >= 3.13
- pyfly >= 0.1.0
- fireflyframework-genai >= 26.02.06
- A VLM-capable API key (OpenAI, Anthropic, or Google)

## License

Apache License 2.0 — Copyright 2026 Firefly Software Solutions Inc
