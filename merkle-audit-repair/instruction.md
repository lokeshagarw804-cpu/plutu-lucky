# Merkle Audit Repair — Debugging Task

## Overview

A cryptographic audit verification system processes transaction logs from multiple ledgers, builds a Merkle hash tree from the entries, generates inclusion proofs for each transaction, and then independently verifies those proofs against the tree root. The system is designed to detect any tampering in the transaction record by ensuring each entry can be cryptographically traced to the root hash.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, transaction data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Log Parsing* (`/app/runtime/log_parser.py`) — Reads transaction entries from JSON ledger files in `/app/runtime/data/`. Normalizes fields to string format for consistent hashing.

2. *Leaf Hashing* (`/app/runtime/hasher.py`) — Computes SHA-256 hashes of each transaction's canonical string representation. Also provides the internal node hash function used during tree construction.

3. *Tree Construction* (`/app/runtime/tree_builder.py`) — Builds a complete binary Merkle tree bottom-up from the leaf hashes. Handles odd-count levels by padding before pairing. Stores all padded levels for proof generation.

4. *Proof Generation* (`/app/runtime/proof_engine.py`) — Produces inclusion proofs by walking the stored tree levels. Each proof step contains a sibling hash and a direction flag indicating which side the sibling is on.

5. *Audit Verification* (`/app/runtime/auditor.py`) — Independently reconstructs each leaf hash from the transaction data, then walks the proof path upward, combining hashes according to direction flags. Compares the computed root against the known tree root.

## Problem

The system produces output but the audit consistently fails — all transactions report as unverified despite the tree being built from the same data. The root hash exists and the proof structures have the correct depth, but proof verification always rejects.

## Expected Correct Output

When all defects are resolved:
- All 7 transactions from both ledger files are processed
- The Merkle tree has depth 4 (levels with 8, 4, 2, 1 nodes including padding)
- All 7 inclusion proofs verify successfully against the root
- The audit report shows status "pass" with verified_count = 7

## Output Schema

### /app/runtime/output/tree_state.json

| Field | Type | Description |
|-------|------|-------------|
| leaf_count | integer | Number of original transaction leaves |
| tree_depth | integer | Number of levels in the tree |
| root_hash | string | SHA-256 root hash of the Merkle tree |
| leaf_hashes | array[string] | Ordered list of leaf hash values |

### /app/runtime/output/proofs.json

| Field | Type | Description |
|-------|------|-------------|
| total_proofs | integer | Number of inclusion proofs generated |
| proofs | object | Map of leaf index to proof step array |
| proofs[idx][].sibling_hash | string | Hash of the sibling node at this level |
| proofs[idx][].direction | string | Side the sibling is on: "left" or "right" |

### /app/runtime/output/audit_report.json

| Field | Type | Description |
|-------|------|-------------|
| root_hash | string | The tree root hash used for verification |
| total_transactions | integer | Total transactions audited |
| verified_count | integer | Transactions that passed verification |
| failed_count | integer | Transactions that failed verification |
| results | array | Per-transaction verification results |
| results[].txn_id | string | Transaction identifier |
| results[].leaf_index | integer | Position in the leaf array |
| results[].leaf_hash | string | Recomputed leaf hash used for verification |
| results[].verified | boolean | Whether this proof verified successfully |
| audit_status | string | "pass" if all verified, "fail" otherwise |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/hasher.py | Leaf hash computation and internal node hashing |
| /app/runtime/tree_builder.py | Merkle tree construction with level padding |
| /app/runtime/proof_engine.py | Inclusion proof generation from stored tree |
| /app/runtime/auditor.py | Independent proof verification against root |
| /app/runtime/log_parser.py | Transaction log loading and normalization |
| /app/runtime/run_audit.py | Main entry point orchestrating all stages |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that all inclusion proofs verify successfully against the Merkle root. The tree construction, proof generation, and verification modules must agree on their conventions for the audit to pass. Multiple interacting defects prevent correct verification.
