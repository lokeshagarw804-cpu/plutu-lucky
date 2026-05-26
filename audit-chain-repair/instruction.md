# Audit Chain Verifier Repair — Debugging Task

## Overview

A cryptographic audit log verifier reads entries from multiple independent log streams, computes HMAC-based hash chains for each stream, verifies the integrity of each entry's link to its predecessor, scores the overall and per-stream integrity, and detects tampered entries. The system handles heterogeneous audit stream types and produces both an integrity report and a detailed tamper detection report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, stream data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes audit streams through five stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format stream files from `/app/runtime/data/`, filtering to only streams whose type appears in the active_streams config

2. *Hash Chain Computation* (`/app/runtime/hasher.py`) — For each stream, computes the expected HMAC hash of each entry using the stream's key (truncated to the key_length from the `verification.hmac` configuration section) and the previous entry's hash, forming a verifiable chain

3. *Verification* (`/app/runtime/verifier.py`) — Groups entries into windows of size window_size and reports broken chain links per window. Window count should be ceil(entry_count / window_size) for each stream

4. *Integrity Scoring* (`/app/runtime/integrity_scorer.py`) — Computes per-stream integrity scores independently as valid_count / total_entries for that specific stream, plus an aggregate score across all streams

5. *Tamper Detection* (`/app/runtime/tamper_detector.py`) — Collects all broken-chain entries and sorts them by timestamp. For entries at the same timestamp from different streams, ordering is deterministic using stream_id alphabetically then seq within that stream.

## Problem

The system produces output but with several anomalies:
- Fewer streams and entries are processed than expected given the data files present
- The HMAC key length used for hashing does not match the intended production configuration
- Per-stream integrity scores all show the same value despite streams having different valid/total ratios
- The tampered entry count does not match expectations for the loaded data
- Entries at the same timestamp appear in non-deterministic order across runs

## Expected Correct Output

When all defects are resolved:
- All 43 entries from 4 active streams (access: 15, payment: 12, security: 8, admin: 8) are processed
- The HMAC key length is 32 (from verification.hmac section)
- Per-stream scores differ: access ~0.0667, admin 0.125, payment ~0.0833, security 0.125
- Aggregate score is approximately 0.093 (4 valid out of 43 total)
- Tampered entries at timestamp 1700000300: access comes before payment (alphabetical stream_id)
- Verification produces 4 windows (one per stream, all fit within window_size=50)
- Total tampered entries: 39

## Output Schema

### /app/runtime/output/integrity_report.json

| Field | Type | Description |
|-------|------|-------------|
| stream_count | integer | Number of verified streams |
| streams_verified | array[string] | Sorted list of stream identifiers |
| total_entries | integer | Total entries processed |
| total_valid | integer | Entries with valid chain links |
| total_tampered | integer | Entries with broken chains |
| aggregate_score | float | Overall valid/total ratio |
| per_stream_scores | object | Per-stream integrity scores |
| hmac_key_length | integer | HMAC key length used |

### /app/runtime/output/tamper_report.json

| Field | Type | Description |
|-------|------|-------------|
| tampered_count | integer | Number of tampered entries |
| tampered_entries | array | Sorted list of tampered entry records |
| tampered_entries[].entry_id | string | Entry identifier |
| tampered_entries[].stream_id | string | Source stream |
| tampered_entries[].timestamp | integer | Entry timestamp |
| tampered_entries[].seq | integer | Sequence within stream |
| tampered_entries[].payload | string | Entry payload content |
| verification_windows | array | Per-window verification summaries |
| window_count | integer | Total verification windows |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Verification parameters and stream configuration |
| /app/runtime/loader.py | Stream data loading with type filtering |
| /app/runtime/hasher.py | HMAC-based hash chain computation |
| /app/runtime/verifier.py | Windowed chain verification |
| /app/runtime/integrity_scorer.py | Per-stream and aggregate scoring |
| /app/runtime/tamper_detector.py | Tampered entry detection and ordering |
| /app/runtime/run_audit.py | Main entry point and orchestration |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
