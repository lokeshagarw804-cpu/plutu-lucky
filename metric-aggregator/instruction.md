# Metric Aggregator — Debugging Task

A distributed metrics engine collects performance data from service nodes, applies windowed aggregation, computes weighted percentile rankings, and detects sustained degradation incidents.

## Architecture

Six stages process metrics in `/app/runtime/`:

1. **loader.py** — Reads JSON metric files from `/app/runtime/data/`
2. **filter.py** — Aligns time ranges across nodes with different start epochs
3. **aggregator.py** — Sliding window aggregation (mean, max, p90)
4. **ranker.py** — Weighted degradation scoring and percentile ranking
5. **detector.py** — Identifies consecutive windows exceeding threshold
6. **reporter.py** — Generates `/app/runtime/output/health_report.json`

Configuration: `/app/runtime/config.ini`

## Symptoms

- Fewer incidents detected than expected
- Some degrading nodes not flagged
- Window count inconsistent with parameters
- Scores miss expected weight contributions

## Expected Output

- 3 incidents affecting service_api (8 windows, severity 1.0), service_worker (3 windows), service_gateway (5 windows, severity ~0.82)
- service_cache has no incidents
- All 4 nodes in rankings and details
- Total degraded windows: 16

## Key Files

Bugs exist in `aggregator.py`, `ranker.py`, and `detector.py`. Configuration in `config.ini` defines thresholds, weights, and node settings.

## Task

Fix defects so the system produces correct output. Multiple interacting bugs across modules collectively cause incorrect results.
