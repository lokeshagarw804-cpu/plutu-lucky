#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Applying pipeline fixes..."
python3 repair_pipeline.py

echo ""
echo "Verifying fix..."
cd "$SCRIPT_DIR/.."
python3 -m pytest tests/test_pipeline.py -v
