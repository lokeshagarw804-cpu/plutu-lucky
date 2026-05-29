# PLUTU-LUCKY-CANARY
"""
Pipeline Orchestrator - runs the full register allocation and scheduling
pipeline on all input programs, producing an optimization report.

Pipeline stages:
1. Load programs and machine specification
2. Liveness analysis (backward dataflow)
3. Interference graph construction
4. Graph coloring register allocation
5. Move coalescing
6. Instruction scheduling
7. Report generation
"""

import json
import os
import copy
from typing import Dict, List, Any

from .ir_utils import build_program_from_json, Program
from .liveness_analyzer import analyze_liveness
from .interference_graph import build_interference_graph, InterferenceGraph
from .graph_coloring import color_graph, ColoringResult
from .spill_manager import handle_spills
from .coalescing_engine import coalesce_moves
from .scheduler import schedule_program
from .cost_model import create_cost_model


def get_data_dir() -> str:
    """Locate the data directory."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "data")


def get_output_dir() -> str:
    """Locate (and create) the output directory."""
    base = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base, "output")
    os.makedirs(out, exist_ok=True)
    return out


def load_machine_spec() -> dict:
    """Load machine specification from JSON."""
    path = os.path.join(get_data_dir(), "machine_spec.json")
    with open(path, "r") as f:
        return json.load(f)


def load_program(filename: str) -> dict:
    """Load a program from JSON."""
    path = os.path.join(get_data_dir(), filename)
    with open(path, "r") as f:
        return json.load(f)


def get_precolored_map(program: Program, machine_spec: dict) -> Dict[str, int]:
    """Determine precolored register constraints from the program.

    Instructions with precolored_def field force their definition
    to a specific physical register.
    """
    precolored = {}
    reg_names = machine_spec["register_names"]

    for block in program.blocks.values():
        for instr in block.instructions:
            if instr.precolored_def:
                reg_name = instr.precolored_def
                if reg_name in reg_names:
                    color = reg_names.index(reg_name)
                    for d in instr.defs:
                        precolored[d] = color

    return precolored


def count_instructions(program: Program) -> int:
    """Count total instructions across all blocks."""
    total = 0
    for block in program.blocks.values():
        total += len(block.instructions)
    return total


def count_registers_used(coloring: Dict[str, int]) -> int:
    """Count distinct physical registers used."""
    if not coloring:
        return 0
    return len(set(coloring.values()))


def process_program(program_data: dict, machine_spec: dict) -> Dict[str, Any]:
    """Run the full pipeline on a single program.

    Returns a dictionary of optimization metrics.
    """
    num_registers = machine_spec["num_registers"]
    cost_model = create_cost_model(machine_spec)

    # Build IR
    program = build_program_from_json(program_data)

    # Stage 1: Liveness Analysis
    live_in, live_out, live_ranges = analyze_liveness(program)

    # Stage 2: Build Interference Graph
    precolored_map = get_precolored_map(program, machine_spec)
    graph = build_interference_graph(
        program, live_in, live_out, live_ranges, precolored_map
    )
    interference_edges = graph.get_num_edges()

    # Stage 3: Graph Coloring
    total_spills = 0
    coloring_rounds = 0
    max_alloc_rounds = 5

    for alloc_round in range(max_alloc_rounds):
        result, rounds = color_graph(graph, num_registers)
        coloring_rounds += rounds

        if result.success:
            break

        # Handle spills
        spill_count = handle_spills(program, graph, result.spilled)
        total_spills += len(result.spilled)

        # Re-analyze liveness after spilling
        live_in, live_out, live_ranges = analyze_liveness(program)
        precolored_map = get_precolored_map(program, machine_spec)
        graph = build_interference_graph(
            program, live_in, live_out, live_ranges, precolored_map
        )
    else:
        # Allocation failed after max rounds
        result = ColoringResult()
        result.coloring = {}

    # Stage 4: Move Coalescing
    moves_coalesced = coalesce_moves(program, graph, num_registers)

    # Stage 5: Instruction Scheduling
    schedule_stalls = schedule_program(program, cost_model)

    # Count final metrics
    total_instructions = count_instructions(program)
    registers_used = count_registers_used(result.coloring)

    return {
        "total_instructions": total_instructions,
        "registers_used": registers_used,
        "spills_inserted": total_spills,
        "moves_coalesced": moves_coalesced,
        "schedule_stalls": schedule_stalls,
        "interference_edges": interference_edges,
        "coloring_rounds": coloring_rounds
    }


def run_pipeline() -> dict:
    """Run the complete pipeline on all programs.

    Returns the full optimization report.
    """
    machine_spec = load_machine_spec()

    programs_report = {}

    # Process each program in deterministic order
    program_files = [
        ("alpha", "program_alpha.json"),
        ("beta", "program_beta.json"),
    ]

    total_spills = 0
    total_moves_coalesced = 0
    total_stalls = 0
    all_success = True

    for name, filename in program_files:
        program_data = load_program(filename)
        metrics = process_program(program_data, machine_spec)
        programs_report[name] = metrics

        total_spills += metrics["spills_inserted"]
        total_moves_coalesced += metrics["moves_coalesced"]
        total_stalls += metrics["schedule_stalls"]
        if metrics["spills_inserted"] > 3:
            all_success = False

    report = {
        "programs": programs_report,
        "summary": {
            "total_spills": total_spills,
            "total_moves_coalesced": total_moves_coalesced,
            "total_stalls": total_stalls,
            "allocation_success": all_success,
            "verification_passed": all_success
        }
    }

    return report


def main():
    """Entry point - run pipeline and write report."""
    report = run_pipeline()

    output_dir = get_output_dir()
    report_path = os.path.join(output_dir, "optimization_report.json")

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, sort_keys=False)

    print(f"Optimization report written to {report_path}")
    print(f"  Alpha: {report['programs']['alpha']['registers_used']} regs, "
          f"{report['programs']['alpha']['spills_inserted']} spills, "
          f"{report['programs']['alpha']['moves_coalesced']} coalesced")
    print(f"  Beta:  {report['programs']['beta']['registers_used']} regs, "
          f"{report['programs']['beta']['spills_inserted']} spills, "
          f"{report['programs']['beta']['moves_coalesced']} coalesced")
    print(f"  Total stalls: {report['summary']['total_stalls']}")
    print(f"  Allocation success: {report['summary']['allocation_success']}")


if __name__ == "__main__":
    main()
