<!-- PLUTU-LUCKY-CANARY -->
# Distributed Consensus Ledger Verification System

## Overview

This system implements a distributed consensus ledger verification pipeline that processes financial transactions, verifies Byzantine fault-tolerant (BFT) quorum consensus, detects equivocation among validators, and produces a comprehensive audit report.

The pipeline consists of five core modules that work together to verify ledger integrity:

## Modules

### Merkle Engine (`/app/runtime/merkle_engine.py`)

Builds Merkle trees from transaction batches to produce a tamper-evident root hash. Transactions are divided into batches (configured batch size: 16), each batch produces a local Merkle root, and all batch roots are combined into a global root.

### Quorum Verifier (`/app/runtime/quorum_verifier.py`)

Verifies that each consensus round achieved the required BFT quorum. The threshold computation determines the minimum number of approving votes needed for a round to be considered valid.

### Byzantine Detector (`/app/runtime/byzantine_detector.py`)

Analyzes voting records to identify validators exhibiting Byzantine behavior through equivocation detection. A validator is considered Byzantine if they vote for proposals that conflict with the designated round proposal.

### State Machine (`/app/runtime/state_machine.py`)

Processes all transactions sequentially, computing balance transfers and fees. Each transaction deducts `amount + fee` from the sender and credits `amount` to the receiver.

### Balance Reconciler (`/app/runtime/balance_reconciler.py`)

Detects double-spend attempts by computing transaction fingerprints and identifying collisions. Transactions with identical fingerprints are flagged as potential double-spends.

## Configuration (`/app/runtime/config.ini`)

| Section | Key | Value | Description |
|---------|-----|-------|-------------|
| ledger | fee_rate | 0.001 | Transaction fee as fraction of amount |
| ledger | initial_balance | 1000000000 | Starting balance per account |
| consensus | quorum_model | bft | Byzantine fault tolerant model |
| consensus | max_rounds | 8 | Maximum consensus rounds |
| merkle | hash_algorithm | sha256 | Hash function for Merkle tree |
| merkle | batch_size | 16 | Transactions per Merkle batch |
| audit | output_path | /app/runtime/output/audit_report.json | Output location |

## Data Files

- `/app/runtime/data/transactions.json` - 53 transactions between 10 accounts (A0-A9)
- `/app/runtime/data/validators.json` - 10 validator nodes (V0-V9)
- `/app/runtime/data/voting_records.json` - 8 rounds of voting records

## Output Schema (`/app/runtime/output/audit_report.json`)

| Field | Type | Description |
|-------|------|-------------|
| merkle_root | string | SHA-256 hex hash - global Merkle root of all transactions |
| total_transactions | integer | Total number of transactions processed |
| valid_rounds | integer | Number of rounds that achieved quorum |
| total_rounds | integer | Total consensus rounds (8) |
| byzantine_validators | array | Sorted list of validator IDs classified as Byzantine |
| honest_validators | array | Sorted list of validator IDs classified as honest |
| final_balances | object | Mapping of account ID to final integer balance |
| total_fees_collected | integer | Sum of all transaction fees |
| double_spend_detected | integer | Number of double-spend collision detections |
| quorum_failures | integer | Number of rounds that failed to achieve quorum |
| state_hash | string | SHA-256 hex hash of the final state |

## Expected Behavior

When operating correctly, the system should produce:

- A Merkle root computed using standard left-right concatenation with last-leaf padding
- Quorum threshold of `floor(2n/3) + 1` for n participating validators per round
- Byzantine detection limited to validators whose votes conflict with round proposals
- Fees computed with proper rounding for fractional amounts
- Double-spend detection using complete transaction amount in fingerprints

## Problem

The pipeline currently produces incorrect results in the audit report. Multiple modules contain defects that cause wrong values for various fields. The system runs without errors but produces an invalid audit report.

## Task

Identify and fix all defects in the pipeline modules so that the audit report passes validation. The pipeline should be invoked with:

```bash
cd /app
python3 -m runtime.pipeline
```

All source files are located under `/app/runtime/`. The pipeline reads from `/app/runtime/data/` and writes to `/app/runtime/output/audit_report.json`.
