# Sensor Fusion Calibration Pipeline Repair

## Background

You are maintaining a **multi-cluster sensor fusion calibration pipeline** used in an industrial monitoring system. The pipeline processes readings from 42 sensors organized across 5 geographic clusters (alpha, beta, gamma, delta, epsilon), applies normalization, drift compensation, cross-sensor correlation analysis, confidence scoring, and produces a final calibration matrix.

The pipeline was recently refactored to improve performance on large sensor networks, but after the refactor, the calibration output no longer matches expected values. The integration tests are all failing.

## System Architecture

The pipeline consists of the following stages:

1. **Loader** (`loader.py`) — Loads cluster JSON data and builds cross-reference maps
2. **Normalizer** (`normalizer.py`) — Applies z-score normalization with Bessel correction
3. **Drift Compensator** (`drift_compensator.py`) — Applies exponential decay drift correction
4. **Correlator** (`correlator.py`) — Computes Pearson correlation between cross-referenced sensors
5. **Confidence Scorer** (`confidence_scorer.py`) — Scores sensor reliability using network propagation
6. **Matrix Assembler** (`matrix_assembler.py`) — Builds calibration vectors via sliding window
7. **Calibrator** (`calibrator.py`) — Generates final report with precision rounding
8. **Validator** (`validator.py`) — Data quality validation (pre-pipeline, independent)

Entry point: `run_calibration.py`

## Your Task

The pipeline produces incorrect calibration output. Find and fix the bugs so that all integration tests pass. The tests validate the final calibration output against expected statistical properties — they do not test individual pipeline stages in isolation.

## Running

```bash
# Run the pipeline
python3 environment/runtime/run_calibration.py

# Run tests
bash tests/test.sh
```

## Constraints

- Only modify files in `environment/runtime/`
- Do not modify test files or data files
- The pipeline must produce deterministic output
- All 6 integration tests must pass
