# PLUTU-LUCKY-CANARY
"""
Graph Coloring Register Allocator (Chaitin-Briggs style).
Performs simplification by removing low-degree nodes, then assigns colors.
Handles pre-colored nodes (fixed-register constraints) and potential spills.
"""

from typing import Dict, List, Set, Tuple, Optional
from .interference_graph import InterferenceGraph, IGNode


class ColoringResult:
    """Result of a graph coloring attempt."""

    def __init__(self):
        self.coloring: Dict[str, int] = {}
        self.spilled: List[str] = []
        self.success: bool = False
        self.rounds: int = 0


def get_simplify_candidates(graph: InterferenceGraph,
                            num_colors: int,
                            already_simplified: Set[str]) -> List[str]:
    """Find nodes that can be simplified (degree < K).

    Returns nodes with degree less than K that haven't been simplified yet
    and aren't pre-colored.
    """
    candidates = []
    for reg in sorted(graph.nodes.keys()):
        node = graph.nodes[reg]
        if reg in already_simplified:
            continue
        if node.is_precolored:
            continue
        if node.degree < num_colors:
            candidates.append(reg)
    return candidates


def find_potential_spill(graph: InterferenceGraph,
                         already_simplified: Set[str]) -> Optional[str]:
    """Find the best spill candidate using minimum spill weight.

    When no low-degree node exists, we must potentially spill.
    Choose the node with lowest spill weight (least costly to spill).
    """
    best_reg = None
    best_weight = float('inf')

    for reg in sorted(graph.nodes.keys()):
        node = graph.nodes[reg]
        if reg in already_simplified:
            continue
        if node.is_precolored:
            continue
        if node.spill_weight < best_weight:
            best_weight = node.spill_weight
            best_reg = reg

    return best_reg


def simplify_graph(graph: InterferenceGraph,
                   num_colors: int) -> List[Tuple[str, bool]]:
    """Simplify the interference graph by removing low-degree nodes.

    Returns a stack of (register, is_potential_spill) in removal order.
    The stack is used for assignment in reverse order.
    """
    stack = []
    simplified = set()
    # Add precolored nodes to simplified (they don't go on stack)
    for reg, node in graph.nodes.items():
        if node.is_precolored:
            simplified.add(reg)

    total_to_simplify = len(graph.nodes) - len(simplified)

    while len(stack) < total_to_simplify:
        # Try to find low-degree nodes first
        candidates = get_simplify_candidates(graph, num_colors, simplified)

        if candidates:
            # Remove all low-degree nodes
            for reg in candidates:
                simplified.add(reg)
                stack.append((reg, False))
                # Virtually remove from graph (reduce neighbor degrees)
                for neighbor_reg in list(graph.nodes[reg].neighbors):
                    if neighbor_reg not in simplified:
                        # Decrement effective degree
                        pass  # We track via simplified set
        else:
            # No low-degree node: pick a potential spill
            spill_candidate = find_potential_spill(graph, simplified)
            if spill_candidate is None:
                break
            simplified.add(spill_candidate)
            stack.append((spill_candidate, True))

    return stack


def compute_effective_degree(graph: InterferenceGraph, reg: str,
                             removed: Set[str]) -> int:
    """Compute degree considering removed nodes."""
    if reg not in graph.nodes:
        return 0
    count = 0
    for neighbor in graph.nodes[reg].neighbors:
        if neighbor not in removed:
            count += 1
    return count


def assign_colors(graph: InterferenceGraph,
                  stack: List[Tuple[str, bool]],
                  num_colors: int) -> ColoringResult:
    """Assign colors by popping from the stack and choosing available colors.

    Pre-colored nodes already have their color set. For each node popped,
    find a color not used by any already-colored neighbor.
    """
    result = ColoringResult()

    # Track which nodes have been colored during this phase
    colored_set = set()

    # Pre-colored nodes already have their assignments
    for reg, node in sorted(graph.nodes.items()):
        if node.is_precolored and node.color is not None:
            result.coloring[reg] = node.color

    # Pop stack in reverse (last simplified = first assigned)
    for reg, is_potential_spill in reversed(stack):
        node = graph.nodes[reg]

        # Find colors used by neighbors
        used_colors = set()
        for neighbor_reg in sorted(node.neighbors):
            if neighbor_reg not in graph.nodes:
                continue
            neighbor = graph.nodes[neighbor_reg]
            # BUG: Check both that neighbor has a color AND is in colored_set.
            # Pre-colored nodes have their color set from the start but are
            # NOT in colored_set (which only tracks algorithm-colored nodes).
            # This means pre-colored neighbors' colors are never excluded!
            # Fix: should only check neighbor.color is not None
            if neighbor.color is not None and neighbor_reg in colored_set:
                used_colors.add(neighbor.color)

        # Find first available color
        assigned = False
        for color in range(num_colors):
            if color not in used_colors:
                node.color = color
                result.coloring[reg] = color
                colored_set.add(reg)
                assigned = True
                break

        if not assigned:
            # Actual spill
            result.spilled.append(reg)
            node.is_spilled = True

    result.success = len(result.spilled) == 0
    return result


def color_graph(graph: InterferenceGraph,
                num_colors: int,
                max_rounds: int = 10) -> Tuple[ColoringResult, int]:
    """Main graph coloring entry point.

    Performs iterative simplification and assignment. If spills occur,
    returns them for the spill manager to handle.

    Returns (result, num_rounds).
    """
    rounds = 0

    for round_num in range(max_rounds):
        rounds = round_num + 1

        # Simplify
        stack = simplify_graph(graph, num_colors)

        # Assign
        result = assign_colors(graph, stack, num_colors)
        result.rounds = rounds

        if result.success:
            return result, rounds

        # If spills needed, return for spill manager to handle
        return result, rounds

    # Should not reach here
    result = ColoringResult()
    result.rounds = rounds
    return result, rounds
