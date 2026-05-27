# Flow Metric Engine — Debugging Task

A network traffic analysis pipeline reads packet captures from five interfaces, computes windowed bandwidth and latency statistics, builds a summary matrix, and flags anomalous flows using a composite scoring system. The pipeline runs without errors but produces incorrect results across multiple output fields.

## System Environment

- Language: Python 3.11
- Runtime: /app/runtime/ (source modules, config, data, output)
- Tooling: uv and pytest available
- Config: /app/runtime/config.ini

## Architecture

1. **Loading** (`loader.py`) — reads JSON capture files from `/app/runtime/data/`
2. **Bandwidth** (`bandwidth.py`) — windowed throughput calculation
3. **Latency** (`latency.py`) — windowed percentile and jitter computation
4. **Matrix** (`matrix.py`) — builds interface summary with ordering
5. **Anomaly** (`anomaly.py`) — composite scoring and detection

## Symptoms

- Interface ordering in the output matrix does not match expected numeric ordering
- Bandwidth values seem plausible but some downstream calculations are affected
- The anomaly detector flags the wrong number of interfaces or ranks them incorrectly
- Some per-interface metric values differ from expected reference values

## Expected Correct Output

- Interface order: eth0, eth1, eth2, eth10, eth11
- Exactly 2 anomalous interfaces detected (eth10 and eth11)
- eth10 ranked highest with score above 0.9
- eth10 average jitter above 18ms; eth2 jitter below 1ms

## Output Files

- `/app/runtime/output/traffic_matrix.json` — interface summaries
- `/app/runtime/output/anomaly_report.json` — flagged anomalies with scores

## Task

Find and fix the defects in the runtime source files so output matches expected behavior. Multiple modules contain interacting bugs that collectively produce wrong results.
