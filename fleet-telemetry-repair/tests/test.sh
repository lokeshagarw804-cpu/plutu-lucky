#!/bin/bash
cd /app
python3 -m runtime.main || true
mkdir -p /logs/verifier
uv run --with pytest pytest /tests/test_outputs.py -v 2>&1 | tee /logs/verifier/output.log
TEST_EXIT=${PIPESTATUS[0]}
if [ $TEST_EXIT -eq 0 ]; then echo "1" > /logs/verifier/reward.txt; else echo "0" > /logs/verifier/reward.txt; fi
exit $TEST_EXIT
