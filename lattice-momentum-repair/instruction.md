# Lattice Momentum Propagation Simulator

## System Overview

This system implements a lattice Boltzmann momentum propagation simulator for a 7-cell
two-dimensional lattice topology. The simulator reads a propagation event log, applies
streaming, drift, and collision operations to evolve per-cell momentum vectors, then
produces diagnostic reports including regime classification and relaxation scheduling.

## Architecture

The codebase consists of the following modules:

- **parser.py** - Parses the propagation log file (`propagation_log.dat`) into structured
  event records. Handles validation, normalization, and event registry bookkeeping.

- **momentum_engine.py** - Core simulation engine. Maintains per-cell momentum state and
  applies streaming, drift, and collision operations according to the propagation log events.

- **regime_classifier.py** - Analyzes the evolved momentum state to classify pairwise
  interaction regimes between cells and compute relaxation scheduling priorities.

- **report_writer.py** - Generates output artifacts: per-cell state dumps and flow analysis
  reports with digests for validation.

- **orchestrator.py** - Coordinates the pipeline: parse, simulate, classify, report. Manages
  configuration, caching, and diagnostic output channels.

- **calibration.py** - Computes thermal equilibrium constants, lattice parameters, and
  Reynolds number estimates used for diagnostic annotations.

## Data Format

### Input: `propagation_log.dat`

Each line represents one propagation event in the format:

```
<seq_id> -> <cell_id> -> <event_type> -> <payload>
```

Event types:
- `STREAM`: Direct momentum injection. Payload: `delta=<int>`
- `DRIFT`: Thermal drift correction. Payload: `delta=<int>`
- `COLLISION`: Inter-cell momentum exchange. Payload: `neighbor=<cell_id>;state=<key:val,...>`

### Output

Two output files are produced in `/app/runtime/output/`:

1. **lattice_state.jsonl** - One JSON object per cell containing:
   - `cell_id`: Lattice coordinate identifier
   - `momentum_vector`: Dict mapping all cell IDs to integer momentum components
   - `total_events`: Count of events processed for this cell
   - `last_event_step`: Sequence number of last event affecting this cell

2. **flow_report.json** - Analysis results containing:
   - `decoupled_pairs`: List of cell pairs classified as decoupled
   - `decoupled_count`: Number of decoupled pairs
   - `relaxation_priority`: Ordered list of cells for relaxation sweep
   - `magnitude_map`: Per-cell total momentum magnitudes
   - `digest`: SHA-256 hex digest of canonical simulation state

## Observed Issues

The simulation is producing incorrect results across multiple validation dimensions:

1. **Digest Inconsistency**: The simulation produces inconsistent digest values across
   validation runs when compared against reference calibration benchmarks. The aggregate
   momentum state does not match expected steady-state values for this lattice configuration.

2. **Relaxation Scheduling**: The relaxation scheduling algorithm produces suboptimal cell
   visitation patterns that do not correlate with physical intuition about energy distribution
   across the lattice nodes.

3. **Regime Classification**: Inter-cell regime classification metrics deviate from
   theoretical expectations for systems with this topology. The number of classified
   interaction regimes does not match the expected count for a well-evolved lattice state.

## Constraints

- Python 3.11, standard library only
- No external dependencies permitted
- All modules may contain issues; systematic analysis is required
- The propagation log is authoritative and correctly formatted
