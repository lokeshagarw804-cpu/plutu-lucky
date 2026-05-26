# Merkle Audit Verification — Debugging Task

## Overview

A Merkle tree audit verification system processes transaction logs from multiple ledger files, constructs a binary Merkle tree from the transaction records, generates cryptographic inclusion proofs for each transaction, and independently verifies those proofs against the computed root hash. The system produces an audit report summarizing tree structure, proof data, and verification outcomes.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, transaction data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Data*: /app/runtime/data/ (ledger JSON files)

## Architecture

The system processes transaction data through five stages:

1. *Log Parsing* (`/app/runtime/log_parser.py`) — Reads transaction entries from JSON ledger files in `/app/runtime/data/` and assembles them into a deterministic ordered sequence

2. *Leaf Hashing* (`/app/runtime/hasher.py`) — Computes SHA-256 leaf digests from canonical transaction field representations; also provides the node hash function for internal tree nodes using a domain separator

3. *Tree Construction* (`/app/runtime/tree_builder.py`) — Builds a complete binary Merkle tree bottom-up, padding odd-length levels by duplicating the final node

4. *Proof Generation* (`/app/runtime/proof_engine.py`) — Produces inclusion proofs for each leaf, collecting sibling hashes and concatenation directions from leaf to root

5. *Audit Verification* (`/app/runtime/auditor.py`) — Independently reconstructs leaf hashes and walks proof paths to verify each transaction's inclusion in the committed root

## Problem

The system produces output but with several anomalies:
- The computed root hash does not match the expected reference value for the given transaction data
- Proof verification fails for many transactions despite proofs being generated from the same tree
- Transaction ordering appears inconsistent with the natural ledger file numbering
- Some proofs fail only for transactions at certain leaf positions while others verify correctly
- The leaf hashes computed during verification do not match those stored in the tree

## Expected Correct Output

When all defects are resolved:
- The system should load transactions in natural numeric ledger order: ledger_1, ledger_2, ledger_10
- All 11 transactions should produce a tree with depth 5 and root hash `d8a88a3a24ce283e4e8c7ca6ba20b67a99ad8e5ed4ed2694d945341c5c843926`
- All 11 inclusion proofs should verify successfully against the root
- Leaf hashes should be consistent between tree construction and verification stages
- Node hash computation should be consistent between tree building and proof verification

## Output Schema

### /app/runtime/output/audit_result.json

| Field | Type | Description |
|-------|------|-------------|
| tree.root_hash | string | Hex-encoded SHA-256 Merkle root |
| tree.leaf_count | integer | Number of transaction leaves |
| tree.depth | integer | Number of levels in the tree |
| tree.level_sizes | array[int] | Node count at each level |
| proofs | object | Map of tx_id to proof data |
| proofs[tx_id].leaf_hash | string | Leaf digest for the transaction |
| proofs[tx_id].leaf_index | integer | Position in the leaf level |
| proofs[tx_id].proof_path | array | Sibling hashes and directions |
| verification.total_proofs | integer | Number of proofs checked |
| verification.valid_count | integer | Proofs that verified |
| verification.invalid_count | integer | Proofs that failed |
| verification.results | object | Map of tx_id to boolean |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/log_parser.py | Transaction log loading and ordering |
| /app/runtime/hasher.py | Leaf and node hash computation |
| /app/runtime/tree_builder.py | Merkle tree construction |
| /app/runtime/proof_engine.py | Inclusion proof generation |
| /app/runtime/auditor.py | Independent proof verification |
| /app/runtime/run_audit.py | Main orchestration entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
