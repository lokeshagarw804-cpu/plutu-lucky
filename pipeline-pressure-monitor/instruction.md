# Pipeline Pressure Monitor — Debugging Task

A pipeline pressure monitoring system reads sensor data from segments, computes pressure gradients (dP/dt), aggregates in rolling windows, and detects anomalous events. The system runs with `python3 -m runtime.run_pipeline` from `/app/`. Configuration is in `/app/runtime/config.ini`.

## Pipeline Stages

1. `loader.py` — Loads segment JSON files from `/app/runtime/data/`
2. `segment_mapper.py` — Averages multi-sensor readings per segment
3. `interpolator.py` — Cubic spline upsampling (boundary: clamped)
4. `gradient_calculator.py` — Central finite difference dP/dt
5. `aggregator.py` — Sliding window statistics over gradients
6. `threshold_engine.py` — Detects sustained threshold exceedances, classifies as "surge" or "leak"

## Symptoms

- Gradient magnitudes are implausibly small (wrong denominator)
- Rolling windows miss the final sample in each window
- Negative gradient events (leaks) are not detected
- All events classified as "surge" regardless of direction
- Interpolation uses natural boundary instead of configured clamped

## Expected Correct Output

- Segment order: seg_1, seg_2, seg_3, seg_4, seg_10
- Total events: 4 (2 surges, 2 leaks)
- seg_1, seg_10: surge events; seg_3: leak events
- seg_2, seg_4: no events
- Highest gradient magnitude: seg_3

## Your Task

Fix defects in `/app/runtime/` source files so output matches expected behavior. Multiple modules contain interacting bugs.
