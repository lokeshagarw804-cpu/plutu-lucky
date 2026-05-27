# Pipeline Flow Monitor — Debugging Task

A pipeline flow monitoring system processes sensor data from five pipe segments. It computes expected pressure drops, detects anomalies, classifies faults, and writes a health report. The system runs without errors but produces incorrect output.

## System overview

The system has six processing stages: data loading, pressure calculation (Hagen-Poiseuille), flow aggregation, segment ordering, anomaly detection, and classification with severity scoring. Multiple interacting defects cause the final output to diverge from expected values.

## Expected correct output

When all defects are resolved, `/app/runtime/output/pipeline_report.json` must contain:

- `segment_order`: `["seg_1","seg_2","seg_3","seg_10","seg_11"]`
- `total_pressure_anomalies`: 19
- `total_leaks`: 7
- `total_blockages`: 12
- `max_severity`: approximately 0.5125

And `/app/runtime/output/flow_summary.json` must show `total_volume` ≈ 0.0299.

## Key files

| File | Role |
|------|------|
| config.ini | Parameters, thresholds, weights |
| flow_aggregator.py | Volume computation |
| anomaly_detector.py | Anomaly flagging logic |
| segment_sorter.py | Segment ordering |
| leak_classifier.py | Fault classification and severity |
| pressure_calc.py | Expected pressure drop computation |
| main.py | Orchestration entry point |

## Your task

Find and fix defects in the runtime source files under `/app/runtime/` so that both output files match the expected values above. Run with `python3 -m runtime.main` from `/app`.
