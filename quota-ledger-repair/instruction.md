# Resource Quota Allocation Ledger — Debugging Task

## Overview

You are debugging a resource quota allocation ledger system that processes cloud resource allocation requests from organizational teams, validates them against configured policy limits, verifies their cryptographic integrity, computes priority scores, and produces a structured allocation report.

The system is currently producing incorrect output. Your task is to identify and fix all defects so that the output matches the expected behavior.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Architecture

The system consists of cooperating modules under `/app/runtime/`:

| Module | Responsibility |
|--------|---------------|
| `/app/runtime/ledger_loader.py` | Loads team request files from data directory |
| `/app/runtime/integrity_checker.py` | Validates HMAC-SHA256 signatures on requests |
| `/app/runtime/quota_validator.py` | Checks requests against quota policy limits |
| `/app/runtime/priority_scorer.py` | Assigns priority scores using exponential decay |
| `/app/runtime/report_builder.py` | Assembles the allocation report |
| `/app/runtime/run_allocator.py` | Main entry point |
| `/app/runtime/config.ini` | System configuration |

## Input Data

Team allocation request files are in `/app/runtime/data/`. Each file contains requests with fields: `request_id`, `team`, `tier`, `requested_units`, `payload`, `signature`, `submitted_at`, `priority_group`.

## Output Schema

### /app/runtime/output/allocation_report.json

| Field | Type | Description |
|-------|------|-------------|
| `summary` | object | Aggregate statistics |
| `summary.total_requests` | integer | Total requests processed |
| `summary.approved_count` | integer | Requests passing all checks |
| `summary.rejected_count` | integer | Requests rejected |
| `summary.integrity_pass` | integer | Requests with valid signatures |
| `summary.integrity_fail` | integer | Requests with invalid signatures |
| `summary.team_count` | integer | Distinct teams |
| `batch_order` | list[string] | Filenames in processing order |
| `requests` | list[object] | Per-request results |
| `requests[].request_id` | string | Request identifier |
| `requests[].integrity_valid` | boolean | Signature check result |
| `requests[].quota_status` | string | "approved" or "rejected" |
| `requests[].rejection_reason` | string or null | Rejection reason |
| `requests[].priority_score` | float | Computed priority score |
| `requests[].priority_group` | string | Organizational group |

## Expected Correct Output

- Total requests: 38
- All signatures must verify (0 integrity failures)
- Requests exceeding quota limits must be rejected (8 rejections expected)
- Approved requests: 30
- Root team priority score: 100.0
- Teams: 3
- Batch processing must follow natural file ordering

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output. Multiple modules contain defects that collectively produce incorrect results.
