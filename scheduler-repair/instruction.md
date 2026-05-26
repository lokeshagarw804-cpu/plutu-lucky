# Job Scheduler Repair — Debugging Task

## What this is

A priority-based job scheduler for distributed workers. It reads job queues, dispatches jobs based on priority and deadlines, simulates execution across worker nodes, and reports on scheduling quality.

## Environment

- Python 3.11, working dir `/app`, source in `/app/runtime/`, output written to `/app/runtime/output/`
- pytest available globally

## Processing stages

1. **Dispatch** — Load jobs from priority queues, sort them for optimal scheduling, assign to workers respecting affinity.
2. **Execute** — Simulate job execution on assigned workers, track completion times, flag deadline violations.
3. **Report** — Compute per-worker utilization stats and overall scheduling metrics.

## Symptoms

Jobs are being scheduled in the wrong order. Deadline violation counts seem off. Worker utilization numbers don't add up — they're way too low given the workload.

## Expected output

- `/app/runtime/output/schedule.json`: list of objects with fields `job_id` (str), `worker` (str), `start_ms` (int), `finish_ms` (int), `on_time` (bool)
- `/app/runtime/output/report.json`: object with `total_jobs` (int), `on_time_count` (int), `violation_count` (int), `worker_utilization` (dict mapping worker name to float)

## Key files

| File | Purpose |
|------|---------|
| `/app/runtime/dispatcher.py` | Priority sorting and job assignment |
| `/app/runtime/executor.py` | Execution simulation and deadline checks |
| `/app/runtime/reporter.py` | Stats computation |

## Task

Find and fix the bugs so the scheduler produces correct output. There are multiple issues across the codebase — read carefully.
