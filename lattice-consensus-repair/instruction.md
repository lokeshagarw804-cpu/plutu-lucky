# Lattice Consensus Repair — Debugging Task

## Overview

A distributed consensus analyzer processes transaction logs from multiple validator nodes, constructs a DAG (directed acyclic graph) lattice representing causal ordering, computes stake-weighted confirmation weights, and determines which transactions have achieved finality. The system models a DAG-based consensus protocol where validators issue transactions that reference previous transactions from any validator, forming a lattice structure.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, validator data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Processing Stages

1. *Loading* (`/app/runtime/loader.py`) — Reads validator transaction logs from `/app/runtime/data/`. Each validator file contains transactions with parent references, timestamps, and stake weights. Only validators listed in the configuration are processed.

2. *DAG Construction* (`/app/runtime/dag_builder.py`) — Merges transactions from all loaded validators into a unified DAG. Transactions are sorted in causal order by timestamp, then by validator identifier, then by sequence number for deterministic traversal when multiple transactions share a timestamp.

3. *Weight Computation* (`/app/runtime/weight_calculator.py`) — Computes confirmation weight for each transaction by walking forward through the DAG. Each distinct confirming validator contributes their stake weight only once, at the earliest round in which they first reference the transaction (directly or transitively). This prevents double-counting a validator's stake across multiple rounds.

4. *Finality Checking* (`/app/runtime/finality_checker.py`) — Determines whether a transaction has reached finality based on the quorum threshold defined in the `consensus.finality` configuration section and the confirmation depth (how many rounds ahead the transaction has been confirmed).

5. *Reporting* (`/app/runtime/consensus_reporter.py`) — Generates a finality map (per-transaction details in causal order) and a consensus summary with per-validator statistics.

## Problem

The system produces output but with several anomalies:
- The total transaction count is lower than expected given the number of validator log files present in the data directory
- Finality decisions appear overly strict, with fewer transactions reaching finality than the protocol parameters should allow
- Some early transactions show unexpectedly high confirmation weights suggesting multiple counting
- The ordering of transactions in the finality map is not fully deterministic when multiple validators issue transactions at the same timestamp

## Expected Correct Output

When all defects are resolved:
- All 4 validators should be loaded (53 total transactions)
- The finality map should contain entries for all 53 transactions in deterministic causal order
- Exactly 12 transactions should achieve finality status
- Validator 1 and 2 should each have 5 finalized transactions
- Validator 3 should have 2 finalized transactions
- Validator 4 should have 0 finalized transactions (joins late, insufficient depth)
- The consensus summary should show a finality rate of 0.2264

## Output Schema

### /app/runtime/output/finality_map.json

| Field | Type | Description |
|-------|------|-------------|
| tx_id | string | Unique transaction identifier |
| validator_id | string | Issuing validator identifier |
| round | integer | DAG round number |
| timestamp | integer | Transaction timestamp |
| is_final | boolean | Whether transaction reached finality |
| normalized_weight | float | Confirmation weight normalized by total stake |
| depth_reached | integer | Maximum confirmation depth reached |

### /app/runtime/output/consensus_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_transactions | integer | Total transactions in DAG |
| total_finalized | integer | Count of finalized transactions |
| finality_rate | float | Ratio of finalized to total |
| total_validators | integer | Number of active validators |
| validator_stats | object | Per-validator statistics |
| validator_stats[].validator_id | string | Validator identifier |
| validator_stats[].total_transactions | integer | Transactions from this validator |
| validator_stats[].finalized_count | integer | Finalized transactions from this validator |
| validator_stats[].stake | float | Validator stake weight |
| validator_stats[].finality_rate | float | Per-validator finality ratio |
| rounds_processed | integer | Maximum round number processed |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Network and consensus parameters |
| /app/runtime/loader.py | Validator log loading and filtering |
| /app/runtime/dag_builder.py | DAG construction and causal ordering |
| /app/runtime/weight_calculator.py | Stake-weighted confirmation computation |
| /app/runtime/finality_checker.py | Quorum-based finality decisions |
| /app/runtime/consensus_reporter.py | Report generation |
| /app/runtime/run_consensus.py | Main entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect results.
