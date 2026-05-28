# Consensus Ledger Repair
<!-- PLUTU-LUCKY-CANARY -->

## Overview

You are debugging a distributed consensus ledger verification system. The system processes cryptocurrency-like transactions through a pipeline of verification modules that work together to ensure consistency, detect Byzantine behavior, and reconcile final balances.

The pipeline runs without errors but produces incorrect output. There are bugs hidden in the codebase that cause wrong computation results. Your task is to identify and fix all bugs so that the system produces correct, internally consistent output.

## System Architecture

The verification pipeline (`/app/runtime/pipeline.py`) orchestrates 8 modules in sequence:

### Utility Modules

1. **`/app/runtime/crypto_utils.py`** - Cryptographic primitives including `HashAccumulator` (stateful hash builder with domain separation), `MerkleHasher` (leaf/node hashing), hex utilities, batch hashing, and chain hashing. Used by merkle_engine.py and state_machine.py for hash operations.

2. **`/app/runtime/validator_registry.py`** - `ValidatorRegistry` class managing validator state: stake weights, participation tracking, epoch rotation logic, and eligibility checks. Used by quorum_verifier.py and byzantine_detector.py for validator lookups.

3. **`/app/runtime/audit_trail.py`** - `AuditLogger` class maintaining a hash-chain audit trail of all pipeline operations. Provides tamper-evident logging with integrity verification. Used by pipeline.py for operation tracking.

### Core Verification Modules

4. **`/app/runtime/merkle_engine.py`** - Computes Merkle tree roots for transaction batches. Processes transactions in batches of 10, computing independent roots for each batch. Features batch context management with domain separation salt for the genesis batch.

5. **`/app/runtime/quorum_verifier.py`** - Implements BFT (Byzantine Fault Tolerance) quorum verification. Checks that sufficient stake weight has approved proposals in each consensus round using the 2/3+1 threshold formula. Tracks participation and computes safety margins.

6. **`/app/runtime/byzantine_detector.py`** - Detects Byzantine validators by analyzing voting patterns. Identifies validators that voted for proposals different from the round's canonical proposal. Applies threshold filtering and ratio caps to limit false positives.

7. **`/app/runtime/state_machine.py`** - Processes transactions through a ledger state machine. Handles balance tracking, fee computation, nonce validation, and state transition recording. Maintains account balances across all transactions.

8. **`/app/runtime/balance_reconciler.py`** - Reconciles transaction history with final balances. Computes canonical transaction fingerprints, detects double-spends, identifies nonce gaps, and verifies balance consistency.

## Data Files

- **`/app/runtime/data/transactions.json`** - 53 transactions between 10 accounts (A0-A9), with amounts ranging from 1000 to 100000009, nonces 1-6.
- **`/app/runtime/data/validators.json`** - 10 validators (V0-V9) with varying stake weights (80-130), public keys, and metadata.
- **`/app/runtime/data/voting_records.json`** - Voting records for 8 consensus rounds. Each record has a nested structure with outer metadata and an inner `vote` object containing the actual vote details.

## Configuration

**`/app/runtime/config.ini`** contains parameters for all modules including batch sizes, fee rates, thresholds, and algorithm selections.

## Pipeline Output

The pipeline writes `/app/runtime/output/audit_report.json` containing:
- Merkle roots for each transaction batch
- Per-round quorum verification results
- Byzantine validator detection results
- Final account balances and state hash
- Balance reconciliation status and fingerprint root

## Task

Find and fix all bugs in the codebase. The corrected system should produce internally consistent output where:
- Merkle roots are computed independently per batch (no cross-batch contamination)
- Quorum thresholds are computed relative to the correct stake base
- Byzantine detection correctly identifies only truly malicious validators
- Fee computations use proper rounding without precision loss
- Transaction fingerprints use a deterministic canonical field ordering

## Constraints

- All code must use Python standard library only (no pip packages in runtime)
- Do not modify the data files
- Do not modify the test file
- The pipeline must run without errors after your fixes
- Write your fix as a Python script at `/app/solution/repair_consensus.py` that patches the source files and re-runs the pipeline
