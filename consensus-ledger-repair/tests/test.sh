#!/bin/bash
# PLUTU-LUCKY-CANARY
set -e

echo "Building Docker image..."
docker build -t consensus-test -f environment/Dockerfile environment/

echo "Running pipeline and tests..."
docker run --rm \
  -v "$(pwd)/tests:/tests" \
  consensus-test \
  bash -c 'cd /app && python3 -m runtime.pipeline && uv run --with pytest pytest /tests/test_consensus_ledger.py -v'

echo "All tests passed!"
