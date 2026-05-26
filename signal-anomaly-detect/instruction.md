# Signal Anomaly Detection — Debugging Task

## What this is

Industrial sensor monitoring pipeline. Reads time-series data from three stations, applies sliding-window smoothing, extracts frequency-domain features, and flags anomalous readings based on statistical thresholds.

## Environment

- Python 3.11, working dir `/app`, source in `/app/runtime/`, output goes to `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Ingest** — Load sensor JSONL files from each monitoring station.
2. **Smooth** — Apply overlapping sliding windows. Where windows overlap, the maximum smoothed value for each timestamp should be retained.
3. **Spectrum** — Compute frequency-domain magnitudes using a simplified discrete Fourier transform.
4. **Detect** — Flag anomalies where feature scores exceed a configured threshold. Uses sample variance for normalization.

## Symptoms

Very few or no anomalies detected. Frequency magnitudes appear underestimated. Variance-based scores seem slightly off.

## Expected output

- `/app/runtime/output/anomalies.json`: list of objects with `station` (str), `ts_ms` (int), `score` (float), `frequency_band` (int)
- `/app/runtime/output/summary.json`: object with `total_anomalies`, `stations_affected`, `max_score`, `avg_score`

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/spectrum.py` | Frequency feature extraction |
| `/app/runtime/detector.py` | Threshold-based anomaly scoring |
| `/app/runtime/smoother.py` | Sliding window smoothing |
| `/app/runtime/config.ini` | Parameters and thresholds |

## Task

Find and fix the bugs preventing correct anomaly detection. There are multiple interacting defects across the pipeline — fixing one alone will not produce correct results.
