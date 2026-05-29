<!-- PLUTU-LUCKY-CANARY -->
# Register Allocator and Instruction Scheduler Debugging Task

## Overview

You are debugging a **register allocator and instruction scheduler** for a custom bytecode VM. The system implements Chaitin-Briggs graph coloring register allocation with move coalescing and list scheduling for pipeline stall minimization.

The pipeline processes bytecode programs through several optimization stages and produces an optimization report. The system currently produces **incorrect results** due to bugs in the implementation. Your task is to find and fix the bugs so the pipeline produces the correct optimization metrics.

## System Architecture

The pipeline at `/app/runtime/pipeline.py` orchestrates the following stages:

1. **Load** programs from `/app/runtime/data/` (JSON bytecode format) and machine specification
2. **Liveness Analysis** (`/app/runtime/liveness_analyzer.py`) - backward dataflow with PHI nodes
3. **Interference Graph** (`/app/runtime/interference_graph.py`) - build from live ranges, compute spill weights
4. **Graph Coloring** (`/app/runtime/graph_coloring.py`) - Chaitin-Briggs register allocation
5. **Spill Management** (`/app/runtime/spill_manager.py`) - insert spill/reload for failed coloring
6. **Move Coalescing** (`/app/runtime/coalescing_engine.py`) - eliminate redundant copies
7. **Instruction Scheduling** (`/app/runtime/scheduler.py`) - minimize pipeline stalls
8. **Report Generation** - output `/app/runtime/output/optimization_report.json`

## Module Descriptions

| Module | Path | Purpose |
|--------|------|---------|
| `pipeline.py` | `/app/runtime/pipeline.py` | Main orchestrator, loads data, runs stages |
| `liveness_analyzer.py` | `/app/runtime/liveness_analyzer.py` | Backward dataflow liveness with worklist |
| `interference_graph.py` | `/app/runtime/interference_graph.py` | Build interference graph, compute spill weights |
| `graph_coloring.py` | `/app/runtime/graph_coloring.py` | Chaitin-Briggs graph coloring allocator |
| `spill_manager.py` | `/app/runtime/spill_manager.py` | Spill/reload insertion when coloring fails |
| `coalescing_engine.py` | `/app/runtime/coalescing_engine.py` | Briggs conservative move coalescing |
| `scheduler.py` | `/app/runtime/scheduler.py` | List scheduling with dependency analysis |
| `cost_model.py` | `/app/runtime/cost_model.py` | Pipeline cost and latency estimation |
| `ir_utils.py` | `/app/runtime/ir_utils.py` | IR representation and utility functions |

## Input Data

- `/app/runtime/data/machine_spec.json` - 8 physical registers (r0-r7), r0/r1 precolored, pipeline latencies
- `/app/runtime/data/program_alpha.json` - 4 blocks with loop (PHI nodes, precolored call result)
- `/app/runtime/data/program_beta.json` - 4 blocks with if/else (copy coalescing, anti-dependencies)

## Expected Correct Output

After fixing all bugs, `/app/runtime/output/optimization_report.json` should contain:

```json
{
  "programs": {
    "alpha": {
      "total_instructions": 13,
      "registers_used": 7,
      "spills_inserted": 0,
      "moves_coalesced": 0,
      "schedule_stalls": 4,
      "interference_edges": 36,
      "coloring_rounds": 1
    },
    "beta": {
      "total_instructions": 15,
      "registers_used": 6,
      "spills_inserted": 0,
      "moves_coalesced": 2,
      "schedule_stalls": 6,
      "interference_edges": 31,
      "coloring_rounds": 1
    }
  },
  "summary": {
    "total_spills": 0,
    "total_moves_coalesced": 2,
    "total_stalls": 10,
    "allocation_success": true,
    "verification_passed": true
  }
}
```

## Output Schema

The optimization report has the following structure:

| Field | Type | Description |
|-------|------|-------------|
| `programs.<name>.total_instructions` | int | Total instructions after optimization |
| `programs.<name>.registers_used` | int | Distinct physical registers assigned |
| `programs.<name>.spills_inserted` | int | Number of spill/reload pairs needed |
| `programs.<name>.moves_coalesced` | int | Register copies eliminated |
| `programs.<name>.schedule_stalls` | int | Pipeline stall cycles from scheduling |
| `programs.<name>.interference_edges` | int | Edges in the interference graph |
| `programs.<name>.coloring_rounds` | int | Iterations of simplify-select-spill |
| `summary.total_spills` | int | Sum of spills across all programs |
| `summary.total_moves_coalesced` | int | Sum of coalesced moves |
| `summary.total_stalls` | int | Sum of schedule stalls |
| `summary.allocation_success` | bool | True if all programs allocated successfully |
| `summary.verification_passed` | bool | True if allocation is consistent |

## Running the Pipeline

```bash
cd /app
python3 -m runtime.pipeline
```

This generates `/app/runtime/output/optimization_report.json`.

## Key Concepts

- **Liveness Analysis**: A register is live at a program point if its value may be used before being redefined. PHI nodes at loop headers define values that come from different predecessors.
- **Interference Graph**: Two registers interfere (cannot share a physical register) if they are simultaneously live at any program point.
- **Graph Coloring**: Assign K colors (physical registers) to nodes such that no two adjacent nodes share a color. K=8 for this machine.
- **Spill Weight**: Priority metric for selecting which register to spill. Higher weight means more costly to spill.
- **Move Coalescing**: Eliminate copy instructions by assigning source and destination to the same physical register, when safe.
- **Briggs Criterion**: Coalescing is safe if the merged node has fewer than K neighbors of significant degree (degree >= K).
- **Anti-dependency (WAR)**: Instruction i reads a register that instruction j (later) writes. Prevents reordering j before i.
- **Pre-colored Registers**: Registers with fixed physical assignments (e.g., r0 for return values).

## Constraints

- Python standard library only (no external packages)
- Pipeline must be deterministic (same output every run)
- 8 physical registers available
- r0 and r1 are pre-colored (return value, stack pointer)
