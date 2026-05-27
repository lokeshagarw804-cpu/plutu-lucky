#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Run pytest with the installed Python that has pytest
PYTHON="/opt/toolchains/.pyenv/versions/3.10.20/bin/python"

if ! command -v $PYTHON &> /dev/null; then
    # Fallback: try any python with pytest
    for ver in 3.10.20 3.11.15 3.12.13 3.13.13 3.14.4; do
        PYTHON="/opt/toolchains/.pyenv/versions/$ver/bin/python"
        if $PYTHON -c "import pytest" 2>/dev/null; then
            break
        fi
    done
fi

$PYTHON -m pytest tests/test_pipeline.py -v
