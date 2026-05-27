# Flow Metric Engine — Debugging Task

A traffic analysis pipeline reads packet captures from five network interfaces, computes per-window bandwidth and latency stats, builds a summary matrix, and flags anomalous flows. It runs but gives wrong results.

## What's broken

- Bandwidth numbers are off by roughly three orders of magnitude
- The jitter metric doesn't match the documented definition (mean absolute difference of consecutive latency samples)
- Interface ordering in the matrix is wrong — eth10 and eth11 sort before eth2
- The anomaly detector never flags anything despite clearly bursty interfaces

## Expected correct behavior

- Interface order: eth0, eth1, eth2, eth10, eth11 (numeric sort on suffix)
- Bandwidth should be in the range of thousands to tens-of-thousands bytes/sec
- eth10 and eth11 should both be flagged as anomalous (2 total)
- eth10 must have the highest anomaly score (above 0.9)

## Files

| File | Role |
|------|------|
| /app/runtime/config.ini | Parameters and interface list |
| /app/runtime/loader.py | Reads JSON packet captures |
| /app/runtime/bandwidth.py | Windowed throughput calculation |
| /app/runtime/latency.py | Percentile and jitter computation |
| /app/runtime/matrix.py | Builds the traffic summary |
| /app/runtime/anomaly.py | Composite scoring and detection |
| /app/runtime/main.py | Entry point |

## Output files

- `/app/runtime/output/traffic_matrix.json` — interface summaries
- `/app/runtime/output/anomaly_report.json` — flagged interfaces with scores

Fix the bugs in the runtime source files so output matches expected behavior above.
