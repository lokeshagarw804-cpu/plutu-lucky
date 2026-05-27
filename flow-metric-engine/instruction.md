# Flow Metric Engine — Debugging Task

A packet flow analysis pipeline classifies traffic by size category, computes windowed distributions, scores risk per window, and flags violations exceeding a threshold. The system runs without crashing but produces incorrect outputs across multiple stages.

## System Environment

- Language: Python 3.11
- Runtime: /app/runtime/
- Tooling: uv and pytest available
- Config: /app/runtime/config.ini

## Architecture

1. **Loading** (`loader.py`) — reads per-flow JSON captures
2. **Classification** (`classifier.py`) — assigns packets to size categories based on configured boundaries
3. **Aggregation** (`aggregator.py`) — computes per-window category fractions using sliding window
4. **Scoring** (`scorer.py`) — produces composite risk scores from category weights and latency
5. **Reporting** (`reporter.py`) — detects violations and computes per-flow statistics

## Symptoms

- Total violation counts differ from expected values
- Per-flow violation ratios are either zero or impossibly large
- Window counts per flow do not match expected sliding window behavior
- Category classification of boundary-value packets appears inconsistent
- Some flows that should have violations show none, and vice versa

## Expected Correct Output

- Total windows analyzed: 484 (121 per flow)
- Total violations: 152
- flow_delta: 105 violations, ratio between 0.85 and 0.90
- flow_beta: 47 violations, ratio between 0.35 and 0.42
- flow_alpha and flow_gamma: zero violations
- Top-ranked flow (by peak score): flow_delta

## Output Files

- `/app/runtime/output/violation_report.json`
- `/app/runtime/output/classification_summary.json`

## Task

Fix the defects so output matches expected behavior. Multiple modules have interacting bugs.
