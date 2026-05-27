# Flow Meter Calibration — Debugging Task

## Overview

A calibration pipeline reads voltage/temperature data from industrial flow meters, converts voltages to flow rates via a cubic polynomial, applies temperature compensation, groups readings into time intervals, and checks compliance against operational flow limits. The system currently produces incorrect output.

## Environment

- Python 3.11, runtime at `/app/runtime/`
- Config: `/app/runtime/config.ini`
- Entry point: `python3 -m runtime.main`
- Tools: uv, pytest available system-wide

## Pipeline Stages

1. **loader.py** — reads meter JSON files from `data/`
2. **calibrator.py** — polynomial voltage-to-flow conversion
3. **compensator.py** — temperature correction
4. **aggregator.py** — groups readings into time intervals
5. **reporter.py** — compliance checking against limits

## Symptoms

- Overall compliance results are wrong
- Some meters flagged incorrectly as non-compliant
- Violation intervals don't match expected values
- Meter ordering in output doesn't follow expected convention

## Expected Output

When all defects are fixed:
- Meter order: meter_1, meter_3, meter_7, meter_12, meter_20
- 4 compliant meters, 1 non-compliant (meter_20)
- meter_20 has violations at intervals 1 and 2
- 56 total readings processed, 15 total intervals

## Output Files

- `/app/runtime/output/calibration_results.json` — full compliance report with meter_order, total_meters, compliant_count, non_compliant_count, meters array
- `/app/runtime/output/summary.json` — summary with total_meters, compliant_count, meter_order, total_readings_processed, total_intervals

## Your Task

Identify and fix defects in the runtime source files so the pipeline produces correct output. Multiple modules contain interacting defects.
