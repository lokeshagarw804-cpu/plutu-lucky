#!/bin/bash
LOG_ROOT=/logs/verifier
mkdir -p "$LOG_ROOT" 2>/dev/null || true
(printf '%s\n' 0 > "$LOG_ROOT/reward.txt") 2>/dev/null || true
set -eu
write_reward() { (printf '%s\n' "$1" > "$LOG_ROOT/reward.txt") 2>/dev/null || true; }
cleanup_and_reward() {
  exit_code=$?
  mkdir -p "$LOG_ROOT" 2>/dev/null || true
  if [ "$exit_code" -eq 0 ]; then write_reward 1; else write_reward 0; fi
  exit "$exit_code"
}
trap cleanup_and_reward EXIT

cd /app
python3 -m runtime.run_compiler
mkdir -p /logs/verifier
set +e
uv run --with pytest pytest /tests/test_ast.py -v 2>&1 | tee /logs/verifier/output.log
TEST_EXIT=${PIPESTATUS[0]}
set -e
if [ $TEST_EXIT -eq 0 ]; then echo "1" > /logs/verifier/reward.txt; else echo "0" > /logs/verifier/reward.txt; fi
exit $TEST_EXIT
