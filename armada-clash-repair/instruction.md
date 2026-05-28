# Armada Clash Repair

## Overview

You are debugging a naval fleet engagement simulation system. The system tracks 7 armadas (A0 through A6) operating across multiple theater sectors. Each armada maintains an engagement vector that records its operational history and awareness of fleet-wide engagements.

The simulation processes a log of 45 engagement events, computes engagement vectors for each armada, determines which armada pairs can operate autonomously, and establishes a deployment priority ordering.

## System Architecture

The simulation pipeline consists of the following components:

### Data Files

- `/app/runtime/engagements.dat` - Pipe-delimited engagement log containing all 45 theater events. Each record specifies the tick, armada, event type, target (for regroup operations), and sector.

### Processing Modules

- `/app/runtime/parser.py` - Reads and parses the engagement log into structured event records. Straightforward file I/O.

- `/app/runtime/fleet_doctrine.py` - Fleet doctrine configuration framework. Contains formation definitions, tactical stances, engagement rules, fleet composition modeling, sector control tracking, command hierarchy weighting, and morale dynamics. **This module has been fully validated and is confirmed correct.**

- `/app/runtime/vector_engine.py` - Implements the engagement vector tracking system. Each armada maintains a 7-component vector (one component per fleet). Events increment the armada's own component. Regroup operations synchronize awareness from peer armadas.

- `/app/runtime/clash_analyzer.py` - Analyzes engagement vectors to determine fleet autonomy relationships and compute deployment priority ordering.

- `/app/runtime/armada_report.py` - Generates the final tactical assessment report including all vector states, autonomous pair determinations, deployment ordering, and an integrity digest.

- `/app/runtime/orchestrator.py` - Main entry point that coordinates the full pipeline. Processes events in tick order and produces output files.

### Output Files

- `/app/runtime/clash_state.jsonl` - Intermediate state log showing vector evolution after each event.
- `/app/runtime/armada_report.json` - Final tactical assessment report.

## Event Types

- **SKIRMISH** - Local combat engagement, increments the armada's vector component by 1.
- **BARRAGE** - Heavy engagement, increments the armada's vector component by 2.
- **REGROUP** - Synchronization with a peer armada, merges awareness of fleet-wide engagement states.

## Output Schema

The final report (`armada_report.json`) has the following structure:

```json
{
  "vectors": {
    "A0": [int, int, int, int, int, int, int],
    "A1": [...],
    ...
  },
  "autonomous_pairs": [["Ai", "Aj"], ...],
  "deployment_order": ["Ax", "Ay", ...],
  "fleet_count": 7,
  "total_engagements": int,
  "digest": "sha256_hex_string"
}
```

## Known Symptoms

The current simulation produces incorrect results in three areas:

1. **Autonomous pair analysis produces unexpected results** - The system reports far fewer autonomous pairs than expected. Fleet pairs that should be identified as operationally independent are not being recognized.

2. **Deployment ordering does not reflect fleet engagement depth** - The deployment priority appears to be based on a metric that does not capture the full extent of each armada's operational engagement history.

3. **Integrity digest fails validation** - The SHA256 digest in the report does not match the expected value when recomputed from the report contents, suggesting upstream analytical errors propagate into the digest computation.

## Environment

- Python 3.11 (stdlib only at runtime)
- Global system-wide tooling: uv and pytest are available
- Entry point: `python3 /app/runtime/orchestrator.py`
- Tests: `pytest /tests/test_armada_clash.py`

## Constraints

- All vector components start at base value 3
- There are exactly 7 armadas in the theater
- The engagement log contains exactly 45 events
- The orchestrator processes events strictly in tick order
