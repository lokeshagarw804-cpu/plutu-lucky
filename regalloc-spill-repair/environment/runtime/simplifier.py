"""Graph simplification using Chaitin-Briggs algorithm.

The simplification phase iteratively removes nodes from the interference
graph that can be trivially colored. A node with degree less than K
(number of available registers) can always be colored, since even in
the worst case its neighbors use at most K-1 colors.
"""

import configparser
import os


def load_num_registers():
    """Load number of available registers from config."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read(config_path)
    return int(config.get("regalloc", "num_registers"))


def simplify_graph(adjacency, spill_costs):
    """Perform iterative simplification of the interference graph.
    
    Returns:
        stack: list of (variable, neighbors) tuples in removal order
        spilled: set of variables that must be spilled
    
    Algorithm:
        1. Find a node with degree <= K (can be trivially colored)
        2. Push it onto the stack with its current neighbors
        3. Remove it from the graph (reduce neighbors' degrees)
        4. Repeat until no more simplifiable nodes
        5. Remaining nodes are potential spill candidates
    """
    num_registers = load_num_registers()
    
    # Work on a copy of the adjacency list
    working = {var: set(neighbors) for var, neighbors in adjacency.items()}
    
    stack = []
    spilled = set()
    
    while working:
        # Find a node that can be simplified (degree <= K)
        simplifiable = None
        for var in sorted(working.keys()):
            if len(working[var]) <= num_registers:
                simplifiable = var
                break
        
        if simplifiable is not None:
            # Push onto stack and remove from graph
            neighbors = working[simplifiable].copy()
            stack.append((simplifiable, neighbors))
            
            # Remove from all neighbor lists
            for neighbor in neighbors:
                if neighbor in working:
                    working[neighbor].discard(simplifiable)
            
            del working[simplifiable]
        else:
            # No simplifiable node found - must spill
            # Choose the variable with lowest spill cost
            best_spill = min(
                working.keys(),
                key=lambda v: spill_costs.get(v, float("inf"))
            )
            
            # Remove spilled variable from graph
            neighbors = working[best_spill].copy()
            for neighbor in neighbors:
                if neighbor in working:
                    working[neighbor].discard(best_spill)
            
            del working[best_spill]
            spilled.add(best_spill)
    
    return stack, spilled
