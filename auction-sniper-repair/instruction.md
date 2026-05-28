# Auction Sniper Repair

## Overview

An auction sniper simulation processes competitive bidding events for 7 automated bots, computes bid activity vectors, classifies bot independence relationships, and determines optimal execution ordering. The pipeline produces a JSONL state file and a JSON strategy report.

The system is currently producing incorrect results. The strategy report shows **0 independent bot pairs** (expected: significantly more) and the **execution order** does not reflect proper activity-based priority. Additionally, the **integrity digest** does not match expected values, indicating vector computation errors.

## System Architecture

The simulation pipeline consists of the following components:

### Files (all located at `/app/runtime/`):

| File | Status | Purpose |
|------|--------|---------|
| `auction_log.dat` | ✅ CORRECT | Semicolon-separated event log (45 events, 7 bots) |
| `event_parser.py` | ✅ CORRECT | Parses the auction log into structured records |
| `auction_types.py` | ✅ CORRECT | Type definitions, enums, profile classes |
| `auction_orchestrator.py` | ✅ CORRECT | Pipeline coordinator (main entry point) |
| `bid_tracker.py` | ❌ BUGGY | Computes bid activity vectors |
| `strategy_evaluator.py` | ❌ BUGGY | Classifies independence and computes ordering |
| `auction_report.py` | ❌ BUGGY | Generates report (uses strategy_evaluator) |

### Pipeline Flow

```
auction_log.dat → event_parser.py → bid_tracker.py → strategy_evaluator.py → auction_report.py
                                          ↓                                         ↓
                                   bid_state.jsonl                         strategy_report.json
```

## Running the Simulation

```bash
python3 /app/runtime/auction_orchestrator.py
```

Global system-wide tooling: `uv` and `pytest` are available.

## Output Format

### `bid_state.jsonl` — Per-event state records

Each line is a JSON object:
```json
{"tick": 1, "bot_id": "bot_alpha", "event_type": "SPOT_BID", "vector": "4;3;3;3;3;3;3", "own_component": 4, "sync_count": 0, "total_events": 1}
```

### `strategy_report.json` — Classification report

```json
{
  "session_summary": {"total_bots": 7, "total_events": 45, "bot_ids": [...]},
  "activity_vectors": {"bot_alpha": {"vector": [...], "own_component": N, "total_weight": N}, ...},
  "independence_analysis": {"independent_pair_count": N, "total_possible_pairs": 21, "independent_pairs": [...], ...},
  "execution_plan": {"order": [...], "activity_weights": {...}},
  "integrity": {"digest": "16-char-hex", ...}
}
```

## Observed Symptoms

1. **Independence count = 0**: The report shows zero independent bot pairs, but given the event distribution, multiple pairs should qualify as independent.

2. **Execution order mismatch**: Expected first bot is `bot_epsilon` (lowest activity) but actual first bot differs. Expected last bot is `bot_gamma` but actual differs.

3. **Own-component deficit**: Bots with SYNC_INTEL events show lower own-component values than expected. For example, `bot_alpha` shows own=11 but based on its 4 SPOT_BID (+4), 2 SURGE_BID (+4), plus base (3), the expected minimum is 11 — but the actual correct value accounting for all activity should be 12.

4. **Digest mismatch**: Expected digest is `818b1acf0fc89d5e` but actual is `4cd9418a34b7eadb`.

## Event Types

- **SPOT_BID**: Standard bid placement
- **SURGE_BID**: Premium aggressive bid
- **SYNC_INTEL**: Intelligence synchronization from peer bots

## Bot Roster

| Bot | Total Events | SYNC Events |
|-----|-------------|-------------|
| bot_alpha | 7 | 1 |
| bot_beta | 7 | 1 |
| bot_gamma | 7 | 1 |
| bot_delta | 6 | 1 |
| bot_epsilon | 6 | 0 |
| bot_eta | 6 | 1 |
| bot_zeta | 6 | 1 |
