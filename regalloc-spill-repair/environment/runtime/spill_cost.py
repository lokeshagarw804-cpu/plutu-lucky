"""Compute spill costs for variables based on usage patterns.

Spill cost determines the penalty of spilling a variable to memory.
Variables with higher spill cost should be prioritized for register
allocation, while low-cost variables are better spill candidates.
"""

import configparser
import os


def load_spill_config():
    """Load spill weight configuration."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(config_path)
    return int(config.get("regalloc", "spill_base_weight"))


def compute_variable_usage(blocks):
    """Count uses and defs for each variable, tracking loop depth.
    
    Returns dict mapping variable -> {uses, defs, max_loop_depth}
    """
    usage = {}
    
    for block in blocks:
        loop_depth = block.get("loop_depth", 0)
        
        for instr in block["instructions"]:
            dest = instr.get("dest")
            if dest:
                if dest not in usage:
                    usage[dest] = {"uses": 0, "defs": 0, "max_loop_depth": 0}
                usage[dest]["defs"] += 1
                usage[dest]["max_loop_depth"] = max(
                    usage[dest]["max_loop_depth"], loop_depth
                )
            
            for src in instr.get("srcs", []):
                if src not in usage:
                    usage[src] = {"uses": 0, "defs": 0, "max_loop_depth": 0}
                usage[src]["uses"] += 1
                usage[src]["max_loop_depth"] = max(
                    usage[src]["max_loop_depth"], loop_depth
                )
    
    return usage


def compute_spill_costs(blocks, adjacency):
    """Compute spill cost for each variable.
    
    Formula: cost = (uses + defs) * base_weight * loop_depth_factor / degree
    
    The loop depth factor increases cost exponentially for variables in
    deeply nested loops, making them less desirable to spill.
    """
    base_weight = load_spill_config()
    usage = compute_variable_usage(blocks)
    
    costs = {}
    for var, info in usage.items():
        degree = len(adjacency.get(var, set()))
        if degree == 0:
            degree = 1  # Avoid division by zero
        
        use_def_count = info["uses"] + info["defs"]
        loop_depth = info["max_loop_depth"]
        
        # Apply loop nesting factor: deeper nesting = higher cost
        loop_factor = base_weight * loop_depth if loop_depth > 0 else 1
        
        cost = use_def_count * loop_factor / degree
        costs[var] = round(cost, 4)
    
    return costs
