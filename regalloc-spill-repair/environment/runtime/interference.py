"""Build the interference graph from live intervals.

Two variables interfere if their live intervals overlap. The interference
graph is an undirected graph where edges connect interfering variables.
"""


def intervals_overlap(interval_a, interval_b):
    """Check if two intervals overlap using exclusive-end semantics.
    
    Intervals are assumed to be half-open [start, end) — a variable
    whose interval ends at position N is NOT live at position N itself.
    Two intervals [s1, e1) and [s2, e2) overlap iff s1 < e2 and s2 < e1.
    """
    start_a, end_a = interval_a
    start_b, end_b = interval_b
    return start_a < end_b and start_b < end_a


def build_interference_graph(intervals):
    """Build an interference graph from variable live intervals.
    
    Returns:
        adjacency: dict mapping each variable to set of interfering variables
        edges: set of (var_a, var_b) tuples representing interference edges
    """
    variables = sorted(intervals.keys())
    adjacency = {var: set() for var in variables}
    edges = set()
    
    for i in range(len(variables)):
        for j in range(i + 1, len(variables)):
            var_a = variables[i]
            var_b = variables[j]
            
            if intervals_overlap(intervals[var_a], intervals[var_b]):
                adjacency[var_a].add(var_b)
                adjacency[var_b].add(var_a)
                edge = tuple(sorted([var_a, var_b]))
                edges.add(edge)
    
    return adjacency, edges


def get_degree(adjacency, variable):
    """Get the degree of a variable in the interference graph."""
    return len(adjacency.get(variable, set()))


def get_max_degree(adjacency):
    """Get the maximum degree in the graph."""
    if not adjacency:
        return 0
    return max(len(neighbors) for neighbors in adjacency.values())
