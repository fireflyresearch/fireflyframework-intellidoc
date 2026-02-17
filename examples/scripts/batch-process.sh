#!/usr/bin/env bash
# Batch processing — process all documents in a directory.
set -euo pipefail

# Usage: ./batch-process.sh <directory> [model]
DIR="${1:?Usage: $0 <directory> [model]}"
MODEL="${2:-anthropic:claude-sonnet-4-5-20250929}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${DIR}/results"

echo "=== Batch Processing ==="
echo "Directory: $DIR"
echo "Model:     $MODEL"
echo "Output:    $OUTPUT_DIR"
echo ""

mkdir -p "$OUTPUT_DIR"

# Process all documents with ad-hoc types and schema
intellidoc batch "$DIR" \
    --model "$MODEL" \
    --document-types "@${SCRIPT_DIR}/../document-types/financial-types.json" \
    --schema "@${SCRIPT_DIR}/../schemas/financial-fields.json" \
    --output "$OUTPUT_DIR" \
    --pretty

echo ""
echo "Results written to $OUTPUT_DIR"
