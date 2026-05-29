#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
if [ ! -f /app/runtime/output/lattice_state.jsonl ]; then
    python3 -c "import sys; sys.path.insert(0, '/app/runtime'); from orchestrator import main; main()"
fi
set +e
uv run --with pytest pytest -v /tests/test_lattice_momentum.py
TEST_EXIT=$?
set -e
if [ "$TEST_EXIT" -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
cat /logs/verifier/reward.txt
exit "$TEST_EXIT"
