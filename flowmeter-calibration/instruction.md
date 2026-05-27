# Flow Meter Calibration — Debugging Task

## What This Is

A calibration pipeline reads voltage/temperature data from 5 industrial flow meters, converts voltages to flow rates via a cubic polynomial, applies temperature compensation, groups readings into 60-second intervals, and checks compliance against flow limits.

## Environment

- Python 3.11, runtime at `/app/runtime/`
- Config: `/app/runtime/config.ini`
- Run with: `python3 -m runtime.main`
- Tools available: uv, pytest

## Pipeline Stages

1. **loader.py** — reads meter JSON files from `data/`
2. **calibrator.py** — polynomial voltage-to-flow: coefficients are `a0,a1,a2,a3` (low-to-high order), so `flow = a0 + a1*V + a2*V^2 + a3*V^3`
3. **compensator.py** — temperature correction: `flow * (1 + factor * (temp - ref_temp))`
4. **aggregator.py** — groups by interval index `floor(timestamp / 60)`
5. **reporter.py** — checks compensated flow against min/max limits, orders meters numerically

## Symptoms

- Flow values are way too high for meters with voltage > 2.0
- meter_20 should have 2 compliance violations but doesn't show the right count
- Meter ordering in output doesn't match expected numeric order
- Interval reading counts are off by one for some meters

## Expected Correct Output

- Meter order: meter_1, meter_3, meter_7, meter_12, meter_20
- 4 compliant meters, 1 non-compliant (meter_20)
- meter_20 has violations at intervals 1 and 2
- 56 total readings processed, 15 total intervals

## Output Files

- `/app/runtime/output/calibration_results.json`
- `/app/runtime/output/summary.json`

## Your Task

Find and fix all bugs in the runtime source files so the pipeline produces correct output.
