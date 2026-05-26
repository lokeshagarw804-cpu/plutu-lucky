# Resource Quota Allocation Ledger — Debugging Task

## Overview

You are debugging a **resource quota allocation ledger** system that processes cloud resource allocation requests from organizational teams, validates them against configured policy limits, verifies their cryptographic integrity, computes priority scores, and produces a structured allocation report.

The system is currently producing incorrect output. Your task is to identify and fix all defects so that the test suite passes completely.

## System Architecture

Global system-wide tooling is implemented as a set of cooperating Python modules under `/app/runtime/`. The system-wide allocation workflow proceeds through these stages:

1. **Ledger Loading** (`/app/runtime/ledger_loader.py`) — Reads team allocation request files from the data directory in deterministic batch order.
2. **Integrity Verification** (`/app/runtime/integrity_checker.py`) — Validates HMAC-SHA256 signatures on each request's payload to ensure data has not been tampered with.
3. **Quota Validation** (`/app/runtime/quota_validator.py`) — Checks each request's allocation units against configured policy limits, marking requests as approved or rejected.
4. **Priority Scoring** (`/app/runtime/priority_scorer.py`) — Assigns priority scores based on each request's organizational distance from the root team, using exponential decay.
5. **Report Building** (`/app/runtime/report_builder.py`) — Aggregates processed requests into the final allocation report with summary statistics.

The main entry point is `/app/runtime/run_allocator.py`.

## Configuration

The system configuration lives at `/app/runtime/config.ini` with the following sections:

- `[ledger]` — Source/output directories and HMAC signing key (base64-encoded)
- `[limits]` — General quota limits (permissive)
- `[limits.strict]` — Strict quota limits for enforcement (max_allocation_units = 2000)
- `[scoring]` — Priority scoring parameters (base_priority, decay_factor, root_team)
- `[report]` — Output formatting options

## Input Data

Team allocation request files are located at `/app/runtime/data/`:
- `team_1.json` — 14 allocation requests
- `team_2.json` — 11 allocation requests
- `team_10.json` — 13 allocation requests

Each request contains:
| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique identifier (REQ-001 through REQ-038) |
| `team` | string | Originating team name |
| `tier` | string | Service tier (gold, silver, or bronze) |
| `requested_units` | integer | Number of allocation units requested |
| `payload` | string | JSON-serialized request details (used for signing) |
| `signature` | string | HMAC-SHA256 hex digest of the payload |
| `submitted_at` | integer | Unix timestamp of submission |
| `priority_group` | string | Organizational group for priority calculation |

## Output Schema

The system writes its report to `/app/runtime/output/allocation_report.json` with this structure:

| Field | Type | Description |
|-------|------|-------------|
| `summary` | object | Aggregate statistics for the entire allocation run |
| `summary.total_requests` | integer | Total number of requests processed |
| `summary.approved_count` | integer | Number of requests that passed all checks |
| `summary.rejected_count` | integer | Number of requests rejected for policy violations |
| `summary.integrity_pass` | integer | Number of requests with valid HMAC signatures |
| `summary.integrity_fail` | integer | Number of requests with invalid HMAC signatures |
| `summary.team_count` | integer | Number of distinct teams in the dataset |
| `summary.teams` | object | Per-team breakdown (total, approved, rejected counts) |
| `batch_order` | list[string] | Filenames in the order they were processed |
| `requests` | list[object] | All processed requests with annotations |

Each processed request in the `requests` list includes all original fields plus:

| Field | Type | Description |
|-------|------|-------------|
| `integrity_valid` | boolean | Whether HMAC signature verification passed |
| `quota_status` | string | "approved" or "rejected" |
| `rejection_reason` | string or null | Reason for rejection (e.g., "over_quota") or null if approved |
| `priority_score` | float | Computed priority score based on organizational distance |

## Expected Counts

When the system is working correctly:
- **Total requests**: 38
- **Integrity failures**: 0 (all signatures valid when key is properly handled)
- **Over-quota rejections**: 8 (requests exceeding the strict limit of 2000 units)
- **Approved requests**: 30
- **Teams**: 3
- **Batch order**: team_1.json, team_2.json, team_10.json (numeric order)

## Priority Scoring Formula

Priority scores use exponential decay from the root team:

```
score = base_priority * (decay_factor ** distance)
```

Where:
- `base_priority` = 100 (from config)
- `decay_factor` = 0.80 (from config)
- `distance` = organizational hops from root team (`platform-core`)

Expected scores:
- `platform-core` (distance 0): 100.0
- `platform-services` (distance 1): 80.0
- `platform-external` (distance 2): 64.0

## Integrity Verification

Each request's `payload` field is signed with HMAC-SHA256. The signing key is stored in `config.ini` under `[ledger] integrity_key` and its encoding is specified by `key_encoding = base64`. The system must properly handle the key encoding when computing HMAC digests.

## Running the System

```bash
cd /app
python3 -m runtime.run_allocator
```

## Validation

The test suite runs 12 tests verifying all aspects of the system output. Fix all defects to achieve a passing test suite.
