# Thermal Anomaly Detection Pipeline - Debug Task

## Background

You are maintaining a thermal anomaly detection pipeline for an industrial facility with four monitored zones. The pipeline processes sensor readings through sliding windows, scores threshold breaches, correlates events across zones, and produces prioritized alert batches.

The system was recently deployed but QA reported multiple issues with the alert output.

## Observed Symptoms

1. **Missing alerts**: The pipeline produces only 7 alerts when the facility's thermal profile should generate 11 distinct alert events. Several zones appear to have their events incorrectly dropped.

2. **Incorrect severity scores**: The `final_score` values for alerts are significantly lower than expected. Zones with multiple weight factors (alpha, beta, delta) show scores that do not account for cumulative weighting.

3. **Alert ordering inconsistency**: When multiple alerts share the same severity level, their ordering is not deterministic. The expected behavior is that same-severity alerts are ordered by descending score, then by ascending timestamp for tie-breaking.

## Expected Correct Output

When functioning properly, the pipeline should produce:
- **11 total alerts** (3 critical, 8 high)
- **Total batch score**: 2368.45
- All four zones should have alerts in the output
- `zone_gamma` should have both a critical and a high alert
- `zone_delta` should have three alerts (all high severity)
- Alert ordering must be deterministic and reproducible

## Files

The pipeline code is in `environment/runtime/`:
- `run_pipeline.py` - Main entry point
- `loader.py` - Sensor data loader
- `window_processor.py` - Sliding window aggregation
- `anomaly_scorer.py` - Weighted severity scoring
- `correlator.py` - Cross-zone event correlation and deduplication
- `alert_builder.py` - Alert batch construction and ordering
- `config.ini` - Pipeline configuration
- `data/` - Sensor data fixtures (do not modify)

## Task

Debug and fix the pipeline so that all tests pass. The test suite validates both aggregate metrics and per-alert correctness.

Run the pipeline: `python3 run_pipeline.py`
Run tests: `python3 -m pytest ../tests/ -v`

## Constraints

- Do NOT modify files in the `data/` directory
- Do NOT modify `config.ini`
- Do NOT modify `loader.py`
- The fix should correct the existing logic, not rewrite the pipeline
