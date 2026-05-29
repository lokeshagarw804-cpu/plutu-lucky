# PLUTU-LUCKY-CANARY
"""
Move Coalescing Engine - eliminates unnecessary register-to-register copies.
Uses the Briggs conservative coalescing criterion: it is safe to coalesce
two nodes if the merged node has fewer than K neighbors of significant
degree (degree >= K).
"""

from typing import Dict, List, Set, Tuple, Optional
from .ir_utils import Program, BasicBlock, Instruction
from .interference_graph import InterferenceGraph, IGNode


class CoalesceCandidate:
    """A pair of registers that could potentially be coalesced."""

    def __init__(self, src: str, dst: str, block_id: int, instr_idx: int):
        self.src = src
        self.dst = dst
        self.block_id = block_id
        self.instr_idx = instr_idx

    def __repr__(self):
        return f"Coalesce({self.src}->{self.dst} at B{self.block_id}:{self.instr_idx})"


def find_move_instructions(program: Program) -> List[CoalesceCandidate]:
    """Find all register-to-register move instructions that are candidates
    for coalescing."""
    candidates = []
    for bid in sorted(program.blocks.keys()):
        block = program.blocks[bid]
        for idx, instr in enumerate(block.instructions):
            if instr.is_move():
                src = instr.get_single_use()
                dst = instr.get_single_def()
                if src and dst and src != dst:
                    candidates.append(CoalesceCandidate(src, dst, bid, idx))
    return candidates


def briggs_criterion(graph: InterferenceGraph, reg_a: str, reg_b: str,
                     num_colors: int) -> bool:
    """Check if coalescing reg_a and reg_b is safe using Briggs criterion.

    Briggs conservative criterion: coalescing is safe if the merged node
    would have fewer than K neighbors of SIGNIFICANT degree.
    A neighbor has significant degree if degree >= K (it cannot be trivially
    simplified).

    Returns True if coalescing is safe (conservative).
    """
    if reg_a not in graph.nodes or reg_b not in graph.nodes:
        return False

    node_a = graph.nodes[reg_a]
    node_b = graph.nodes[reg_b]

    # Merged neighbors = union of both nodes' neighbors minus the pair itself
    merged_neighbors = (node_a.neighbors | node_b.neighbors) - {reg_a, reg_b}

    # Count neighbors with significant degree
    # BUG: Uses > K instead of >= K (off-by-one in the Briggs criterion)
    # A node with degree exactly K is significant because it cannot be
    # trivially simplified (needs K colors, has K neighbors)
    significant_count = 0
    K = num_colors
    for neighbor_reg in sorted(merged_neighbors):
        if neighbor_reg in graph.nodes:
            neighbor_degree = graph.nodes[neighbor_reg].degree
            if neighbor_degree > K:
                significant_count += 1

    # Safe if fewer than K significant-degree neighbors
    return significant_count < K


def george_criterion(graph: InterferenceGraph, reg_a: str, reg_b: str,
                     num_colors: int) -> bool:
    """Check if coalescing is safe using George criterion.

    George criterion: for every neighbor t of reg_a, either t already
    interferes with reg_b, or t has insignificant degree (degree < K).

    This is an alternative criterion, not used by default.
    """
    if reg_a not in graph.nodes or reg_b not in graph.nodes:
        return False

    node_a = graph.nodes[reg_a]
    K = num_colors

    for neighbor_reg in sorted(node_a.neighbors):
        if neighbor_reg == reg_b:
            continue
        if neighbor_reg not in graph.nodes:
            continue
        neighbor = graph.nodes[neighbor_reg]
        # Either neighbor already interferes with reg_b, or has low degree
        if not graph.has_edge(neighbor_reg, reg_b) and neighbor.degree >= K:
            return False

    return True


def perform_coalesce(graph: InterferenceGraph, program: Program,
                     src: str, dst: str) -> bool:
    """Coalesce two registers by merging src into dst.

    - Transfer all edges from src to dst
    - Remove the move instruction
    - Rename all references from src to dst
    """
    if src not in graph.nodes or dst not in graph.nodes:
        return False

    src_node = graph.nodes[src]
    dst_node = graph.nodes[dst]

    # Transfer edges from src to dst
    for neighbor_reg in list(src_node.neighbors):
        if neighbor_reg != dst:
            graph.add_edge(dst, neighbor_reg)

    # Remove src node
    graph.remove_node(src)

    # Rename in program
    _rename_register(program, src, dst)

    return True


def _rename_register(program: Program, old_reg: str, new_reg: str):
    """Rename all occurrences of old_reg to new_reg in the program."""
    for block in program.blocks.values():
        for instr in block.instructions:
            if old_reg in instr.defs:
                instr.defs.discard(old_reg)
                instr.defs.add(new_reg)
            if old_reg in instr.uses:
                instr.uses.discard(old_reg)
                instr.uses.add(new_reg)

    # Update PHI nodes
    for phi in program.phi_nodes:
        if phi.def_reg == old_reg:
            phi.def_reg = new_reg
        phi.operands = [(new_reg if v == old_reg else v, b)
                        for v, b in phi.operands]


def remove_coalesced_moves(program: Program) -> int:
    """Remove move instructions where src and dst are the same register.

    After renaming, some moves become no-ops (mov x, x).
    Returns the number of moves removed.
    """
    removed = 0
    for block in program.blocks.values():
        new_instructions = []
        for instr in block.instructions:
            if instr.is_move():
                src = instr.get_single_use()
                dst = instr.get_single_def()
                if src == dst:
                    removed += 1
                    continue
            new_instructions.append(instr)
        block.instructions = new_instructions
    return removed


def coalesce_moves(program: Program, graph: InterferenceGraph,
                   num_colors: int) -> int:
    """Main coalescing entry point.

    Iteratively finds move instructions and attempts to coalesce using
    the Briggs conservative criterion. Returns total moves coalesced.
    """
    total_coalesced = 0
    max_iterations = 50  # Prevent infinite loops

    for iteration in range(max_iterations):
        candidates = find_move_instructions(program)
        coalesced_this_round = 0

        for candidate in candidates:
            src = candidate.src
            dst = candidate.dst

            # Skip if either no longer exists in graph
            if src not in graph.nodes or dst not in graph.nodes:
                continue

            # Skip if they already interfere
            if graph.has_edge(src, dst):
                continue

            # Skip if either is precolored (can't rename precolored)
            if graph.nodes[src].is_precolored or graph.nodes[dst].is_precolored:
                continue

            # Check Briggs criterion for safety
            if briggs_criterion(graph, src, dst, num_colors):
                if perform_coalesce(graph, program, src, dst):
                    coalesced_this_round += 1

        # Remove any moves that became no-ops
        removed = remove_coalesced_moves(program)
        total_coalesced += removed

        if coalesced_this_round == 0:
            break

    return total_coalesced
