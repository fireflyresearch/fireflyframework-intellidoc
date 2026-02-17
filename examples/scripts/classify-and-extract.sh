#!/usr/bin/env bash
# Classify against ad-hoc types, then extract with inline schema.
set -euo pipefail

# Usage: ./classify-and-extract.sh <file> [model]
FILE="${1:?Usage: $0 <file> [model]}"
MODEL="${2:-anthropic:claude-sonnet-4-5-20250929}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Ad-Hoc Classification + Extraction ==="
echo "File:  $FILE"
echo "Model: $MODEL"
echo ""

# Mode 1: Inline types + inline schema
echo "--- Inline notation ---"
intellidoc process "$FILE" \
    --model "$MODEL" \
    --document-types "invoice:Payment request with line items,receipt:Proof of purchase,contract:Legal agreement" \
    --schema "amount:currency,vendor:text,date:date,reference_number:text" \
    --pretty

echo ""

# Mode 2: JSON files for types and schema
echo "--- JSON file references ---"
intellidoc process "$FILE" \
    --model "$MODEL" \
    --document-types "@${SCRIPT_DIR}/../document-types/financial-types.json" \
    --schema "@${SCRIPT_DIR}/../schemas/financial-fields.json" \
    --pretty

echo ""

# Mode 3: Binary classification (expected type hint)
echo "--- Binary classification ---"
intellidoc process "$FILE" \
    --model "$MODEL" \
    --expected-type invoice \
    --schema "invoice_number:text,total_amount:currency,vendor:text,date:date" \
    --pretty
