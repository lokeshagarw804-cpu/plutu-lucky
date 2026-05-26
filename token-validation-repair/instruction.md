# HMAC Token Batch Validator — Debugging Task

## System Overview

You are working on a system-wide token validation service deployed as part of a larger authentication infrastructure. The validator processes batches of HMAC-signed access tokens and validates them against configurable security policies.

Global system-wide tooling depends on the output of this validator to make authorization decisions. The service must correctly verify cryptographic signatures, enforce expiry policies, compute trust scores, and produce a structured validation report.

## Architecture

The system consists of six modules located at `/app/runtime/`:

| Module | Responsibility |
|--------|---------------|
| `token_loader.py` | Loads token batch JSON files from the data directory |
| `signature_verifier.py` | Validates HMAC-SHA256 signatures using the configured key |
| `policy_checker.py` | Checks token expiry, issuer trust, and scope permissions |
| `trust_scorer.py` | Assigns trust scores with decay based on issuer chain distance |
| `report_builder.py` | Assembles the final validation report with ordering |
| `run_validator.py` | Main entry point orchestrating the workflow |

## Configuration

The system configuration is at `/app/runtime/config.ini`. It contains sections for token source/output paths, signing key configuration, policy parameters, scoring parameters, and output ordering preferences.

Key details:
- The signing key is stored with base64 encoding as indicated by `key_encoding = base64`
- Policy enforcement has both standard and strict parameter sections
- Trust scoring uses an exponential decay model based on issuer chain distance
- The root issuer is `auth-primary` with distance 0

## Data

Token batch files are stored in `/app/runtime/data/` as JSON files. Each batch file contains a `tokens` array where each token has:
- `token_id`: Unique identifier (TOK-001 through TOK-040)
- `payload`: JSON string containing claims (subject, issuer, issued-at, expiry, scopes, JWT ID)
- `signature`: HMAC-SHA256 hex digest of the payload
- `issued_at`: Unix timestamp when the token was issued
- `expires_at`: Unix timestamp when the token expires
- `issuer`: The issuing authority identifier
- `scopes`: List of permission scopes granted

There are 3 batch files containing 40 tokens total.

## Expected Behavior

When functioning correctly, the validator should:
1. Load all batch files in numeric filename order (batch_1, batch_2, batch_10 — not lexicographic)
2. Verify each token's HMAC-SHA256 signature using the base64-decoded signing key — all 40 signatures should be valid
3. Apply the strict security policy (60 second clock drift) to check expiry — exactly 10 tokens should be marked expired
4. Compute trust scores: tokens from root issuer `auth-primary` (distance 0) get score 100.0, `auth-backup` (distance 1) gets 85.0, `auth-legacy` (distance 2) gets 72.25
5. Produce a report at `/app/runtime/output/validation_report.json` with exactly 30 fully valid tokens (signature valid + not expired + policy pass)

## Output Schema

### /app/runtime/output/validation_report.json

The report has the following top-level structure:

| Field | Type | Description |
|-------|------|-------------|
| summary | object | Aggregate counts for the validation run |
| summary.total_tokens | integer | Total tokens processed (should be 40) |
| summary.valid_tokens | integer | Tokens passing all checks (should be 30) |
| summary.expired_tokens | integer | Tokens past strict 60s drift (should be 10) |
| summary.invalid_signatures | integer | Tokens with bad HMAC (should be 0) |
| tokens | array | Per-token detailed results |
| tokens[].token_id | string | Token identifier (TOK-001 through TOK-040) |
| tokens[].batch_source | string | Source batch filename |
| tokens[].signature_valid | boolean | Whether HMAC signature verified |
| tokens[].expired | boolean | Whether token is past expiry + drift |
| tokens[].policy_pass | boolean | Whether token passes all policy checks |
| tokens[].trust_score | float | Computed trust score based on issuer distance |
| batch_count | integer | Number of batch files processed (should be 3) |
| batch_order | array[string] | Filenames in processing order |

## Expected Counts

- Total tokens: 40 (15 from batch_1 + 12 from batch_2 + 13 from batch_10)
- Valid signatures: 40 (all tokens have valid HMAC when key is correctly decoded)
- Expired tokens: 10 (tokens whose expiry is more than 60 seconds before reference time)
- Valid tokens: 30 (signature valid AND not expired AND policy pass)
- Root issuer tokens (auth-primary, score 100.0): 13 tokens

## Current State

The system is producing incorrect results. Multiple modules contain defects that affect signature verification, policy enforcement, trust score computation, and batch processing order. The validator runs without crashing but produces a report with incorrect values.

## Your Task

Identify and fix the defects in the runtime modules so that the validator produces correct output. All fixes should be applied to files under `/app/runtime/`. Do not modify the configuration file or the test infrastructure.

## Reference Time

The system uses a fixed reference time of `1700000000` (Unix timestamp) for all time-based calculations. This is hardcoded in the relevant module.
