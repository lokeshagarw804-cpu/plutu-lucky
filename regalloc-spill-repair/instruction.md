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

1. Process 3 IR blocks containing 20 variables (v0 through v19) total
2. Compute correct live intervals for all variables
3. Build an interference graph with exactly 64 conflict edges
4. The maximum variable degree in the interference graph should be 11
5. Variable v0 should have live interval [0, 8]
6. Variables v7 and v8 have adjacent live ranges — v7 should have degree 4 and v8 should have degree 6
7. Variable v19 (in a depth-2 loop) should have spill cost approximately 13.3333
8. Apply Chaitin-Briggs simplification to identify spill candidates
9. Exactly 6 variables should be spilled: v2, v6, v9, v12, v13, v17
10. Exactly 14 variables should be allocated to registers
11. All 4 registers (R0, R1, R2, R3) must be used
12. Variable v3 must be allocated to register R1
13. Variable v5 must be allocated to register R2
14. Register R0 should be assigned to at least 4 variables
15. Produce a valid allocation using all 4 available registers

The allocation must satisfy the interference constraint: no two variables assigned to the same register may have overlapping live intervals.

## Output Schema

### /app/runtime/output/allocation_report.json

| Field | Type | Description |
|-------|------|-------------|
| variables | object | Per-variable allocation details, keyed by variable name (v0-v19) |
| variables[].interval | array[int, int] | Live interval pair |
| variables[].degree | integer | Number of interfering neighbors in the graph |
| variables[].spill_cost | float | Computed spill priority cost |
| variables[].spilled | boolean | Whether the variable was spilled to stack |
| variables[].register | string | Assigned register name (R0-R3) or "STACK" if spilled |
| variables[].color | integer or null | Assigned color index (0-3) or null if spilled |
| statistics | object | Aggregate allocation statistics |
| statistics.allocated | integer | Number of variables assigned to registers |
| statistics.spilled | integer | Number of variables spilled to stack |
| statistics.registers_used | integer | Number of distinct registers utilized |

### /app/runtime/output/summary.txt

Plain text summary with allocation counts and per-variable assignment listing.

## Constraints

- The system uses K=4 registers (R0, R1, R2, R3)
- Variables that cannot be colored are spilled to STACK
- Spill cost determines which variable to evict when simplification stalls
- Loop nesting should increase spill cost for deeply nested variables (base weight from config)

## System Environment

- Global system-wide tooling: uv and pytest are available

## Notes

- All source files are in `/app/runtime/`
- Data files are in `/app/runtime/data/`
- Output directory is `/app/runtime/output/`
- The system should not crash — it runs to completion but produces wrong results
- Focus on the mathematical relationships between components
