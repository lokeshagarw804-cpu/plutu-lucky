# Lattice Boltzmann Momentum Propagation Simulator

## Overview

This system simulates momentum propagation across a 7-cell hexagonal lattice using the Lattice Boltzmann method. Each cell maintains a momentum vector that evolves through streaming, drift, and collision events recorded in a propagation log.

The simulator reads events from a structured log file, applies them to each cell's momentum state, analyzes flow relationships between cells, and produces a comprehensive report.

## System Architecture

The pipeline consists of the following modules located in `/app/runtime/`:

### Correct Modules (no issues observed)

- **`parser.py`** - Reads and parses the arrow-separated propagation log file (`propagation_log.dat`). Extracts sequence numbers, cell identifiers, event types, and event details into structured records.

- **`orchestrator.py`** - Coordinates the full simulation pipeline. Invokes the parser, builds lattice state, generates reports, and computes the simulation integrity digest.

### Modules Under Investigation

- **`momentum_engine.py`** - Manages per-cell momentum vectors. Each cell starts with a base momentum value of 3 for all 7 components. Streaming and drift events increment the cell's own component. Collision events synchronize momentum knowledge with neighboring cells.

- **`flow_analyzer.py`** - Provides flow coupling predicates and dissipation priority computation. Determines whether cell pairs have coupled or decoupled flow states, and computes the order in which cells should be processed for dissipation.

- **`report_writer.py`** - Generates the flow analysis report by classifying all cell pairs and computing dissipation scheduling priorities.

## Observed Symptoms

1. **Momentum values appear lower than expected after collision events.** Cells that participate in collisions should reflect their active participation in the momentum exchange, but the final momentum components seem to only account for passive information absorption.

2. **The dissipation priority ordering does not reflect actual momentum magnitudes.** The priority list should place high-momentum cells first for dissipation processing, but the current ordering appears disconnected from the cells' total momentum values.

3. **Some cell pairs that should be flagged as decoupled are not.** The decoupled pair count is unexpectedly low. Cells with independent momentum evolution patterns are being classified as coupled when their flow states do not actually interfere with each other.

## Data Format

### Input: `propagation_log.dat`

Arrow-separated format with comment lines starting with `;`:

```
SEQ -> CELL_ID -> EVENT_TYPE -> DETAIL
```

Event types:
- `STREAM` - detail: `delta=N` (streaming increment)
- `DRIFT` - detail: `delta=N` (drift increment)
- `COLLISION` - detail: `neighbor_state=cell_alpha:V;cell_beta:V;...;cell_eta:V`

### Output: `/app/runtime/output/lattice_state.jsonl`

One JSON record per line (sorted by cell_id):

```json
{"cell_id": "cell_alpha", "momentum_vector": {"cell_alpha": N, ...}, "total_events": N}
```

### Output: `/app/runtime/output/flow_report.json`

```json
{
  "total_pairs": 21,
  "decoupled_pairs": [["cell_a", "cell_b"], ...],
  "decoupled_count": N,
  "coupled_pairs": [["cell_a", "cell_b"], ...],
  "coupled_count": N,
  "dissipation_priority": ["cell_x", "cell_y", ...],
  "priority_magnitudes": {"cell_x": N, ...},
  "simulation_digest": "hex_string"
}
```

## Running the Simulation

```bash
cd /app
python3 -c "import sys; sys.path.insert(0, '/app/runtime'); from orchestrator import main; main()"
```

## Validation

The test suite checks structural integrity, momentum computation accuracy, flow analysis correctness, and overall simulation consistency. All 14 tests should pass when the system is operating correctly.
