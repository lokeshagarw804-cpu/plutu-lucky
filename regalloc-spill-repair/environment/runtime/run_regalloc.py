"""Main register allocation driver.

Coordinates the full register allocation process:
  1. Load IR blocks from data files
  2. Compute live intervals for all variables
  3. Build the interference graph
  4. Compute spill costs
  5. Simplify the graph (Chaitin-Briggs)
  6. Color the simplified graph
  7. Generate allocation report
"""

import os
import sys
import configparser

from runtime.loader import load_blocks, get_all_variables
from runtime.liveness import compute_live_intervals
from runtime.interference import build_interference_graph
from runtime.spill_cost import compute_spill_costs
from runtime.simplifier import simplify_graph
from runtime.coloring import assign_colors, format_allocation
from runtime.reporter import generate_report


def load_config():
    """Load runtime configuration."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(config_path)
    return config


def run():
    """Execute the full register allocation process."""
    config = load_config()
    num_registers = int(config.get("regalloc", "num_registers"))
    output_dir = config.get("output", "directory")
    
    # Step 1: Load IR blocks
    blocks = load_blocks()
    variables = get_all_variables(blocks)
    print(f"Loaded {len(blocks)} blocks with {len(variables)} variables")
    
    # Step 2: Compute live intervals
    intervals = compute_live_intervals(blocks)
    print(f"Computed live intervals for {len(intervals)} variables")
    
    # Step 3: Build interference graph
    adjacency, edges = build_interference_graph(intervals)
    print(f"Built interference graph: {len(edges)} edges")
    
    # Step 4: Compute spill costs
    spill_costs = compute_spill_costs(blocks, adjacency)
    print(f"Computed spill costs for {len(spill_costs)} variables")
    
    # Step 5: Simplify graph
    stack, spilled = simplify_graph(adjacency, spill_costs)
    print(f"Simplified: {len(stack)} on stack, {len(spilled)} spilled")
    
    # Step 6: Assign colors
    coloring, color_failed = assign_colors(stack, adjacency, num_registers)
    
    # Variables that failed coloring are also spilled
    all_spilled = spilled | color_failed
    print(f"Colored: {len(coloring)} assigned, {len(all_spilled)} total spilled")
    
    # Step 7: Format and report
    allocation = format_allocation(coloring, all_spilled)
    report = generate_report(
        allocation, intervals, adjacency, spill_costs, output_dir
    )
    
    print(f"\nAllocation complete. Report written to {output_dir}/")
    print(f"  Variables: {report['statistics']['total_variables']}")
    print(f"  Allocated: {report['statistics']['allocated']}")
    print(f"  Spilled: {report['statistics']['spilled']}")
    
    return report


if __name__ == "__main__":
    run()
