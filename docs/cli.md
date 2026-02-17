# CLI Reference

**fireflyframework-intellidoc — Command-Line Interface**

> Copyright 2026 Firefly Software Solutions Inc — Apache License 2.0

---

The `intellidoc` CLI lets you process documents directly from your terminal without
running a web server or database. It uses the same processing engine as the REST API
with in-memory catalog and result storage.

## Installation

The CLI is installed automatically with the package:

```bash
pip install fireflyframework-intellidoc
```

Verify the installation:

```bash
intellidoc --version
intellidoc --help
```

No `web` extra is required — the CLI works with the core package.

## CLI vs REST API

| Feature | CLI (`intellidoc`) | REST API (`pyfly run`) |
|---------|-------------------|----------------------|
| Setup | Zero config | Requires `pyfly.yaml` |
| Storage | In-memory (ephemeral) | Persistent (PostgreSQL, S3, etc.) |
| Catalog | YAML file (optional) | REST API endpoints (optional) |
| Best for | Quick processing, testing, CI/CD, scripts | Production services, multi-user, long-running |
| Batch | Directory-based | Request-based with job tracking |
| Auth | None (local tool) | JWT, API keys (via `security` extra) |
| Async | Not needed (blocking) | Supported with job polling |

## Commands

### `intellidoc process`

Process a single document file.

```bash
intellidoc process <file> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `file` | Path to the document (PDF, PNG, JPG, TIFF, BMP, WebP) |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | Config default | VLM model in `provider:model` format |
| `--api-key` | From env | API key (or set `OPENAI_API_KEY`, etc.) |
| `--fields` | All defaults | Comma-separated catalog field codes to extract |
| `--schema` | - | Inline extraction schema: `name:type,...` or `@file.json` |
| `--document-types` | - | Ad-hoc types for classification: `code:desc,...` or `@file.json` |
| `--expected-type` | Auto-classify | Binary classification hint (is this document of type X?) |
| `--expected-nature` | Any | Narrow classification to this nature |
| `--splitting-strategy` | Config default | `whole_document`, `page_based`, or `visual` |
| `--format` | `json` | Output format: `json`, `table`, `csv` |
| `--output` | stdout | Write results to file instead of stdout |
| `--pretty` | off | Pretty-print JSON output |
| `--quiet` | off | Suppress progress output |

**Examples:**

```bash
# Basic processing
intellidoc process invoice.pdf

# With specific model and API key
intellidoc process invoice.pdf --model openai:gpt-4o --api-key sk-...

# Extract specific fields only
intellidoc process invoice.pdf --fields invoice_number,total_amount,vendor_name

# Binary classification hint — "is this an invoice?"
intellidoc process invoice.pdf --expected-type invoice

# Extraction-only — define fields inline, no classification needed
intellidoc process invoice.pdf \
    --schema "invoice_number:text,total_amount:currency,vendor:text,date:date"

# Ad-hoc types for classification + inline schema
intellidoc process document.pdf \
    --document-types "invoice:Payment request with line items,receipt:Proof of purchase" \
    --schema "amount:currency,vendor:text"

# Binary classification + inline schema
intellidoc process invoice.pdf \
    --expected-type invoice \
    --schema "invoice_number:text,amount:currency"

# Schema from JSON file
intellidoc process invoice.pdf --schema @fields.json

# Output as formatted table
intellidoc process invoice.pdf --format table

# Pretty JSON to file
intellidoc process invoice.pdf --pretty --output result.json

# Narrow classification to financial documents
intellidoc process unknown-doc.pdf --expected-nature financial

# Pipe JSON to jq
intellidoc process invoice.pdf --quiet | jq '.documents[0].extracted_fields'
```

### `intellidoc batch`

Process all supported documents in a directory.

```bash
intellidoc batch <directory> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `directory` | Path to directory containing documents |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | Config default | VLM model in `provider:model` format |
| `--api-key` | From env | API key |
| `--fields` | All defaults | Comma-separated catalog field codes |
| `--schema` | - | Inline extraction schema: `name:type,...` or `@file.json` |
| `--document-types` | - | Ad-hoc types: `code:desc,...` or `@file.json` |
| `--expected-type` | Auto-classify | Binary classification hint for all files |
| `--format` | `json` | Output format: `json`, `table`, `csv` |
| `--output` | stdout | Output directory for per-file results |
| `--parallel` | `4` | Max parallel documents |
| `--pretty` | off | Pretty-print JSON |
| `--quiet` | off | Suppress progress |

**Supported file types:** `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, `.webp`

**Examples:**

```bash
# Process all documents in a folder
intellidoc batch ./invoices/

# Save per-file results to an output directory
intellidoc batch ./invoices/ --output ./results/

# Process with a specific model
intellidoc batch ./scans/ --model anthropic:claude-sonnet-4-5-20250929

# All files are invoices — binary classification hint
intellidoc batch ./invoices/ --expected-type invoice --format table

# Inline schema for all files in the batch
intellidoc batch ./receipts/ --schema "vendor:text,amount:currency,date:date"

# Ad-hoc types + schema
intellidoc batch ./mixed/ \
    --document-types "invoice:Payment request,receipt:Proof of purchase" \
    --schema "amount:currency,vendor:text"

# Quiet mode for scripting
intellidoc batch ./documents/ --quiet --output ./out/ --format json
```

### `intellidoc catalog validate`

Validate a catalog YAML file without processing any documents.

```bash
intellidoc catalog validate <file>
```

**Example:**

```bash
intellidoc catalog validate catalog.yaml
```

Output:
```
  ✓ Catalog is valid: catalog.yaml
    Document types: 3
    Fields:         12
    Validators:     5
```

### `intellidoc catalog show`

Display the contents of a catalog YAML file.

```bash
intellidoc catalog show <file> [--format table|json]
```

**Examples:**

```bash
# Rich table output (default)
intellidoc catalog show catalog.yaml

# JSON output
intellidoc catalog show catalog.yaml --format json
```

## API Key Resolution

The CLI resolves API keys in this order:

1. **`--api-key` flag** — highest priority
2. **Environment variable** — `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY` (based on model provider)
3. **`.env` file** — reads from `.env` in the current directory

```bash
# Via flag
intellidoc process doc.pdf --model openai:gpt-4o --api-key sk-...

# Via environment variable
export OPENAI_API_KEY="sk-..."
intellidoc process doc.pdf

# Via .env file in CWD
echo "OPENAI_API_KEY=sk-..." > .env
intellidoc process doc.pdf
```

## Dynamic Pipeline Modes

The CLI supports the same five pipeline modes as the REST API. The catalog is optional —
you can drive classification and extraction entirely at runtime.

| Mode | Options | Classification | Extraction |
|---|---|---|---|
| **Full catalog** | (none — uses `catalog.yaml`) | Multi-class VLM | Catalog default fields |
| **Ad-hoc types + schema** | `--document-types` + `--schema` | Multi-class VLM | Schema-driven |
| **Binary classification** | `--expected-type` + `--schema` | Single-type VLM | Schema-driven |
| **Extraction-only** | `--schema` only | Skipped | Schema-driven |
| **Mixed** | Catalog + `--document-types` and/or `--schema` | Merged types | Inline schema priority |

### `--schema` Format

Inline notation — comma-separated `name:type` pairs:
```bash
--schema "invoice_number:text,total_amount:currency,vendor:text,date:date"
```

File reference — JSON array of field definitions:
```bash
--schema @fields.json
```

Where `fields.json` contains:
```json
[
  {"name": "invoice_number", "display_name": "Invoice Number", "field_type": "text", "required": true},
  {"name": "total_amount", "display_name": "Total Amount", "field_type": "currency", "description": "The total amount due"}
]
```

Valid field types: `text`, `number`, `date`, `currency`, `boolean`, `email`, `phone`, `address`, `table`, `list`, `enum`, `image_region`

### `--document-types` Format

Inline notation — comma-separated `code:description` pairs:
```bash
--document-types "invoice:A formal payment request,receipt:A proof of purchase"
```

File reference — JSON array of type definitions:
```bash
--document-types @types.json
```

Where `types.json` contains:
```json
[
  {"code": "invoice", "description": "A formal payment request with line items"},
  {"code": "receipt", "description": "A proof of purchase from a store", "nature": "financial"}
]
```

### Field Resolution Priority

When both `--fields` and `--schema` are provided, the priority is:

1. **Inline fields** (`--schema`) — highest priority, always used when present
2. **Catalog field codes** (`--fields`) — resolved from the catalog
3. **Catalog defaults** — from the classified document type (only when confidence meets threshold)

## Catalog YAML Format

When using the CLI with a catalog, document types, fields, and validators are defined in a
`catalog.yaml` file. Place it in the current directory or pass it explicitly. The catalog is
**optional** — if no `catalog.yaml` is present, the CLI works in fully dynamic mode using
`--schema` and `--document-types`.

```yaml
document_types:
  - code: invoice
    name: Commercial Invoice
    description: A commercial invoice for goods or services
    nature: financial
    visual_description: A document with line items, totals, and payment details
    visual_cues:
      - company logo
      - invoice number
      - line items table
      - total amount
    sample_keywords:
      - invoice
      - bill to
      - total
    default_field_codes:
      - invoice_number
      - invoice_date
      - total_amount
      - vendor_name

fields:
  - code: invoice_number
    display_name: Invoice Number
    field_type: text
    required: true
    location_hint: Near the top of the document

  - code: invoice_date
    display_name: Invoice Date
    field_type: date
    required: true
    format_pattern: "YYYY-MM-DD"

  - code: total_amount
    display_name: Total Amount
    field_type: currency
    required: true

  - code: vendor_name
    display_name: Vendor Name
    field_type: text
    required: true

validators:
  - code: invoice_total_check
    name: Total Verification
    validator_type: cross_field
    severity: warning
    config:
      type: sum
      fields: [subtotal, tax_amount]
      total_field: total_amount
      tolerance: 0.01
```

The CLI auto-loads `catalog.yaml` from the current directory at startup. You can also
validate and inspect catalogs with the `catalog validate` and `catalog show` commands.

## Output Formats

### JSON (default)

```bash
intellidoc process invoice.pdf
intellidoc process invoice.pdf --pretty
```

```json
{
  "status": "completed",
  "model_used": "openai:gpt-4o",
  "documents": [
    {
      "document_type": "invoice",
      "confidence": 0.95,
      "fields": {
        "invoice_number": "INV-2026-0042",
        "total_amount": 1250.00
      },
      "validation_passed": true
    }
  ]
}
```

### Table

```bash
intellidoc process invoice.pdf --format table
```

Renders a Rich-formatted table on the terminal with field names, values,
confidence scores, and validation status.

### CSV

```bash
intellidoc process invoice.pdf --format csv
```

Outputs comma-separated values suitable for piping to other tools or importing
into spreadsheets.

## Configuration

The CLI reads `pyfly.yaml` from the current directory if present. Key properties:

```yaml
pyfly:
  shell:
    enabled: true

  intellidoc:
    enabled: true
    default_model: "openai:gpt-4o"
    default_splitting_strategy: "whole_document"
    default_confidence_threshold: 0.7
```

Command-line flags override configuration file values. For example, `--model` overrides
`default_model` from the config.

## CI/CD Integration

The CLI is designed for scripting and automation:

```bash
# Exit code reflects processing success
intellidoc process document.pdf --quiet --output result.json
echo "Exit code: $?"

# Batch process and check results
intellidoc batch ./incoming/ --quiet --output ./processed/ --format json

# Validate catalog before deployment
intellidoc catalog validate catalog.yaml || exit 1

# Extract specific field and use in shell
TOTAL=$(intellidoc process invoice.pdf --quiet --fields total_amount | jq -r '.documents[0].fields.total_amount')
echo "Invoice total: $TOTAL"
```

## Architecture

The CLI boots a headless PyFly application with the same DI container as the web server.
The key difference is the adapter layer:

| Component | Web Server | CLI |
|-----------|-----------|-----|
| Entry point | `pyfly run` (ASGI) | `intellidoc` (Click) |
| Catalog storage | Database (PostgreSQL, etc.) | In-memory (from YAML) |
| Result storage | Database | In-memory |
| Shell adapter | N/A | `IntelliDocShellAdapter` |
| Processing engine | Same `ProcessingOrchestrator` | Same `ProcessingOrchestrator` |

The processing pipeline (ingest, preprocess, split, classify, extract, validate) is
identical in both modes — only the storage adapters differ. Both modes support all five
dynamic pipeline modes (catalog, ad-hoc types, binary classification, extraction-only, mixed).
