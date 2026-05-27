# Register Allocation — Interference Graph and Spill Repair

## Overview

You are debugging a register allocation system for a compiler backend. The system processes function IR (intermediate representation) blocks, performs liveness analysis, builds a variable interference graph, computes spill costs, simplifies the graph using the Chaitin-Briggs algorithm, and assigns registers via graph coloring.

The system is currently producing incorrect allocation results. Your task is to identify and fix the issues so that the allocation output matches the expected behavior for the provided IR blocks.

## System Architecture

The register allocator consists of several cooperating modules:

- `/app/runtime/loader.py` — Loads IR block data from JSON files
- `/app/runtime/liveness.py` — Computes live intervals for all variables
- `/app/runtime/interference.py` — Builds the interference graph from live intervals
- `/app/runtime/spill_cost.py` — Computes spill priority costs for each variable
- `/app/runtime/simplifier.py` — Performs Chaitin-Briggs graph simplification
- `/app/runtime/coloring.py` — Assigns register colors to simplified nodes
- `/app/runtime/reporter.py` — Generates the allocation report
- `/app/runtime/run_regalloc.py` — Main driver coordinating all phases
- `/app/runtime/config.ini` — Configuration (4 registers, base weight, paths)
- `/app/runtime/data/` — Contains IR block JSON files (block_1.json, block_2.json, block_3.json)

## Execution

To run the system:

```bash
cd /app
python3 -m runtime.run_regalloc
```

Output is written to `/app/runtime/output/`:
- `allocation_report.json` — Full allocation details per variable
- `summary.txt` — Human-readable summary

## Expected Behavior

When working correctly, the system should:

1. Process 3 IR blocks containing 20 variables total
2. Compute correct live intervals using half-open interval representation
3. Build an interference graph with the proper number of conflict edges
4. Calculate spill costs that properly account for loop nesting depth
5. Apply Chaitin-Briggs simplification with correct degree thresholds
6. Assign the minimum colors needed without false constraints
7. Produce a valid allocation using all 4 available registers
8. Report the correct number of spilled variables

The allocation must satisfy the interference constraint: no two variables assigned to the same register may have overlapping live intervals.

## Constraints

- The system uses K=4 registers (R0, R1, R2, R3)
- Variables that cannot be colored are spilled to STACK
- Spill cost determines which variable to evict when simplification stalls
- The interference check uses half-open interval overlap semantics
- Loop nesting should exponentially increase spill cost (base weight from config)

## Global system-wide tooling: uv and pytest are available

## Notes

- All source files are in `/app/runtime/`
- Data files are in `/app/runtime/data/`
- Output directory is `/app/runtime/output/`
- The system should not crash — it runs to completion but produces wrong results
- Focus on the mathematical relationships between components
