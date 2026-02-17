# IntelliDoc Examples

Example configurations and scripts demonstrating all five pipeline modes.

## Prerequisites

```bash
pip install fireflyframework-intellidoc
export ANTHROPIC_API_KEY="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"
```

## Pipeline Modes

### 1. Extraction-Only (No Catalog, No Classification)

The simplest mode — define inline fields and extract. No catalog required.

```bash
# Inline notation
intellidoc process document.pdf \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --schema "title:text,author:text,date:date,summary:text" \
    --pretty

# From JSON file
intellidoc process document.pdf \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --schema @schemas/invoice-fields.json \
    --pretty
```

### 2. Ad-Hoc Types + Schema (Runtime Classification)

Classify against types defined at request time, extract with inline schema.

```bash
# Inline notation
intellidoc process document.pdf \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --document-types "invoice:Payment request with line items,receipt:Proof of purchase,contract:Legal agreement" \
    --schema "amount:currency,vendor:text,date:date" \
    --pretty

# From JSON files
intellidoc process document.pdf \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --document-types @document-types/financial-types.json \
    --schema @schemas/financial-fields.json \
    --pretty
```

### 3. Binary Classification + Schema

Provide a single expected type for focused "is this an X?" classification.

```bash
intellidoc process invoice.pdf \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --expected-type invoice \
    --schema "invoice_number:text,total_amount:currency,vendor:text,date:date" \
    --pretty
```

### 4. Full Catalog

Use a `catalog.yaml` for production-grade type definitions, fields, and validators.

```bash
# Place catalog.yaml in the working directory
cp catalog/invoice-catalog.yaml catalog.yaml

intellidoc process invoice.pdf \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --pretty
```

### 5. Mixed Mode (Catalog + Runtime)

Combine catalog types with ad-hoc types and/or inline fields.

```bash
cp catalog/invoice-catalog.yaml catalog.yaml

# Add an ad-hoc type alongside catalog types
intellidoc process document.pdf \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --document-types "utility_bill:Monthly utility bill for electricity or gas" \
    --schema "account_number:text,amount_due:currency,due_date:date" \
    --pretty
```

## File Reference

| Directory | Contents |
|---|---|
| `schemas/` | JSON field definition files for `--schema @file.json` |
| `document-types/` | JSON type definition files for `--document-types @file.json` |
| `catalog/` | Sample `catalog.yaml` files for full catalog mode |
| `scripts/` | Shell scripts demonstrating end-to-end workflows |

## Batch Processing

```bash
# Process a directory of documents
intellidoc batch ./invoices/ \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --schema @schemas/invoice-fields.json \
    --output ./results/ \
    --pretty

# Batch with ad-hoc types
intellidoc batch ./mixed-documents/ \
    --model anthropic:claude-sonnet-4-5-20250929 \
    --document-types @document-types/financial-types.json \
    --schema @schemas/financial-fields.json \
    --output ./results/ \
    --format table
```
