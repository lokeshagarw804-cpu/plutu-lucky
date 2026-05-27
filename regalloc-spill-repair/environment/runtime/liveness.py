"""Compute live intervals for variables across all blocks.

Each variable gets a live interval representing the range of instruction
indices where the variable is active (from first definition to last use).
The interval is half-open: [start, end) where end is the exclusive bound.
This matches the strict-less-than overlap check in the interference module.
"""


def compute_live_intervals(blocks):
    """Compute the live interval for each variable.
    
    Returns a dict mapping variable name -> (start, end) where:
      - start is the instruction index of the first definition
      - end is the exclusive upper bound (last_use index)
      
    Instructions are indexed globally across all blocks in order.
    The end value represents the point where the variable is no longer
    needed, so the interval is [start, end).
    """
    intervals = {}
    global_index = 0
    
    for block in blocks:
        for instr in block["instructions"]:
            # Track definitions
            dest = instr.get("dest")
            if dest:
                if dest not in intervals:
                    intervals[dest] = [global_index, global_index]
                else:
                    intervals[dest][1] = global_index
            
            # Track uses
            for src in instr.get("srcs", []):
                if src not in intervals:
                    intervals[src] = [global_index, global_index]
                else:
                    intervals[src][1] = global_index
            
            global_index += 1
    
    # Convert to tuples
    result = {}
    for var, (start, end) in intervals.items():
        result[var] = (start, end)
    
    return result


def get_variables_live_at(intervals, point):
    """Get all variables that are live at a given instruction index."""
    live = set()
    for var, (start, end) in intervals.items():
        if start <= point <= end:
            live.add(var)
    return live
