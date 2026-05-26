# Signal Processing Station Analyzer — Debugging Task

## Overview

A sensor signal processing system ingests readings from multiple monitoring stations, applies station-specific calibration transforms, computes cross-station correlation coefficients in sliding windows, detects anomalous deviations, and generates structured reports. The system currently produces outputs that violate expected mathematical properties and physical constraints.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Loading* — Reads sensor readings from station JSON files in /app/runtime/data/. Each station file contains timestamped measurements across pressure and temperature channels.

2. *Normalization* — Applies station-specific calibration to raw readings. The calibration section of /app/runtime/config.ini defines per-station offsets. The mode field determines how the offset modifies the raw value. Only stations listed in the configured set are processed.

3. *Windowing* — Creates overlapping time windows for localized signal analysis. Window parameters control the temporal granularity of correlation and detection stages.

4. *Correlation* — Computes Pearson correlation coefficients between station pairs within each window. The reported average correlation for each pair should represent the arithmetic mean of per-window measurements. Valid Pearson coefficients are mathematically bounded in the range [-1.0, 1.0].

5. *Detection* — Identifies readings that deviate significantly from the station mean within each window. The refined detection parameters provide tighter sensitivity for production deployments. Severity quantifies the magnitude relative to the configured threshold.

6. *Reporting* — Generates three output files: anomaly report with entries sorted for deterministic prioritization, correlation matrix with pair statistics, and a processing summary. For anomaly ranking, entries at equal severity are disambiguated by station identifier then timestamp to ensure stable ordering across runs.

## Problem

The system executes without crashes but produces outputs with multiple issues:
- Some station data is excluded from processing despite being configured
- Calibrated values appear to be in an incorrect magnitude range
- Correlation statistics report values outside mathematically valid bounds
- The anomaly detection sensitivity does not match the intended configuration
- Anomaly report ordering is non-deterministic for entries with tied severity

## Expected Correct Output

When functioning correctly:
- All 56 readings from 4 stations are calibrated and processed
- Calibrated pressure values remain within the physical range (approximately 98-104 hPa plus small offsets)
- All correlation coefficients fall within [-1.0, 1.0]
- Anomaly detection uses refined sensitivity parameters
- Anomaly entries are deterministically sorted by (severity descending, station_id ascending, timestamp ascending)

## Output Schema

### /app/runtime/output/anomaly_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_anomalies | int | Count of detected anomalous readings |
| entries | list | Sorted list of anomaly entries |
| entries[].reading_id | string | Source reading identifier |
| entries[].station_id | string | Station that produced the reading |
| entries[].timestamp | string | ISO 8601 measurement timestamp |
| entries[].channel | string | Measurement channel (pressure/temperature) |
| entries[].calibrated_value | float | Value after calibration transform |
| entries[].deviation | float | Statistical deviation from window mean |
| entries[].severity_score | float | Severity ratio (deviation / threshold) |

### /app/runtime/output/correlation_matrix.json

| Field | Type | Description |
|-------|------|-------------|
| total_pairs | int | Number of station pairs analyzed |
| entries | list | Per-pair correlation statistics |
| entries[].pair | string | Pair identifier (stationA:stationB:channel) |
| entries[].avg_correlation | float | Mean correlation across windows, bounded [-1, 1] |
| entries[].window_count | int | Number of windows where pair was computed |
| entries[].total_correlation | float | Sum of per-window correlations |

### /app/runtime/output/processing_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_readings | int | Number of readings after calibration |
| stations_processed | list | Sorted list of station identifiers |
| channels | list | Measurement channels present |
| windows_created | int | Number of time windows |
| total_anomalies | int | Detected anomaly count |
| correlation_pairs | int | Number of correlation pairs |
| anomalies_by_station | object | Anomaly count per station |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_spatial.py | Main entry point, orchestrates processing |
| /app/runtime/loader.py | Reads sensor data from station files |
| /app/runtime/normalizer.py | Calibration transform and station filtering |
| /app/runtime/aligner.py | Temporal windowing |
| /app/runtime/correlator.py | Cross-station correlation computation |
| /app/runtime/event_detector.py | Anomaly detection with threshold |
| /app/runtime/matrix_builder.py | Report generation and output formatting |
| /app/runtime/config.ini | System configuration |
| /app/runtime/data/station_1.json | Alpha station readings (14 records) |
| /app/runtime/data/station_2.json | Beta station readings (14 records) |
| /app/runtime/data/station_3.json | Gamma station readings (14 records) |
| /app/runtime/data/station_4.json | Delta station readings (14 records) |

## Your Task

Identify and fix the defects in the runtime source files under /app/runtime/ that cause station exclusion, incorrect calibration magnitudes, out-of-bounds correlation values, mismatched detection sensitivity, and non-deterministic anomaly ordering.
