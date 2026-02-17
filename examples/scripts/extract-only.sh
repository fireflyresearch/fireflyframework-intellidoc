#!/usr/bin/env bash
# Extract-only mode — no catalog, no classification
# Simplest pipeline mode: define fields inline and extract.
set -euo pipefail

# Usage: ./extract-only.sh <file> [model]
FILE="${1:?Usage: $0 <file> [model]}"
MODEL="${2:-anthropic:claude-sonnet-4-5-20250929}"

echo "=== Extraction-Only Mode ==="
echo "File:  $FILE"
echo "Model: $MODEL"
echo ""

# Inline schema notation
intellidoc process "$FILE" \
    --model "$MODEL" \
    --schema "title:text,author:text,date:date,summary:text" \
    --pretty

echo ""
echo "=== Using a JSON schema file ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
intellidoc process "$FILE" \
    --model "$MODEL" \
    --schema "@${SCRIPT_DIR}/../schemas/invoice-fields.json" \
    --pretty
