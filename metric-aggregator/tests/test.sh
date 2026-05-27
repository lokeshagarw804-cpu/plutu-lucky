#!/bin/bash
mkdir -p /logs/verifier
cd /app
python3 -m runtime.main 2>&1 || true
uv run --with pytest pytest /tests/test_outputs.py -v > /logs/verifier/output.log 2>&1
if [ $? -eq 0 ]; then
    echo "1" > /logs/verifier/reward.txt
else
    echo "0" > /logs/verifier/reward.txt
fi
cat /logs/verifier/output.log
