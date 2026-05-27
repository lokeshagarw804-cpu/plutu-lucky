"""Graph coloring for register assignment.

After simplification, variables are popped from the stack and assigned
colors (registers). Each variable gets the lowest-numbered available
register not already used by any of its colored neighbors.
"""


def assign_colors(stack, adjacency, num_registers):
    """Assign register colors by popping from the simplification stack.
    
    Variables are colored in reverse removal order (last removed = first colored).
    Each variable gets the lowest available color not used by its already-colored
    neighbors in the interference graph.
    
    Returns:
        coloring: dict mapping variable -> register number (0-indexed)
        failed: set of variables that couldn't be colored (need spilling)
    """
    coloring = {}
    failed = set()
    
    # Process stack in reverse (LIFO) order
    for var, original_neighbors in reversed(stack):
        # Collect colors used by already-colored neighbors
        used_colors = set()
        for neighbor in adjacency.get(var, set()):
            if neighbor in coloring:
                used_colors.add(coloring[neighbor])
        
        # Find lowest available color
        assigned = None
        for c in range(num_registers):
            if c not in used_colors:
                assigned = c
                break
        
        if assigned is not None:
            coloring[var] = assigned
        else:
            failed.add(var)
    
    return coloring, failed


def get_register_name(color):
    """Convert a color number to a register name."""
    return f"R{color}"


def format_allocation(coloring, spilled):
    """Format the allocation result for reporting."""
    allocation = {}
    for var, color in sorted(coloring.items()):
        allocation[var] = {
            "register": get_register_name(color),
            "color": color,
            "spilled": False,
        }
    
    for var in sorted(spilled):
        allocation[var] = {
            "register": "STACK",
            "color": -1,
            "spilled": True,
        }
    
    return allocation
