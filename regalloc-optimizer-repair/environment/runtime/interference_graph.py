# PLUTU-LUCKY-CANARY
"""
Interference Graph construction and management.
Builds an interference graph from live ranges where two registers
interfere if they are simultaneously live. Computes node weights
for spill priority decisions.
"""

from typing import Dict, List, Set, Tuple, Optional
from .ir_utils import Program, BasicBlock, Instruction


class IGNode:
    """A node in the interference graph representing a virtual register."""

    def __init__(self, reg: str):
        self.reg = reg
        self.neighbors: Set[str] = set()
        self.color: Optional[int] = None
        self.is_precolored: bool = False
        self.uses: int = 0
        self.degree: int = 0
        self.spill_weight: float = 0.0
        self.is_spilled: bool = False
        self.move_related: bool = False

    def add_neighbor(self, other_reg: str):
        """Add an interference edge to another node."""
        if other_reg != self.reg:
            self.neighbors.add(other_reg)
            self.degree = len(self.neighbors)

    def remove_neighbor(self, other_reg: str):
        """Remove an interference edge."""
        self.neighbors.discard(other_reg)
        self.degree = len(self.neighbors)

    def __repr__(self):
        return (f"IGNode({self.reg}, deg={self.degree}, "
                f"color={self.color}, spill_w={self.spill_weight:.2f})")


class InterferenceGraph:
    """The interference graph for register allocation."""

    def __init__(self):
        self.nodes: Dict[str, IGNode] = {}
        self.edges: Set[Tuple[str, str]] = set()

    def add_node(self, reg: str) -> IGNode:
        """Add a node to the graph (or return existing)."""
        if reg not in self.nodes:
            self.nodes[reg] = IGNode(reg)
        return self.nodes[reg]

    def add_edge(self, reg1: str, reg2: str):
        """Add an interference edge between two registers."""
        if reg1 == reg2:
            return
        edge = (min(reg1, reg2), max(reg1, reg2))
        if edge not in self.edges:
            self.edges.add(edge)
            self.add_node(reg1).add_neighbor(reg2)
            self.add_node(reg2).add_neighbor(reg1)

    def has_edge(self, reg1: str, reg2: str) -> bool:
        """Check if two registers interfere."""
        edge = (min(reg1, reg2), max(reg1, reg2))
        return edge in self.edges

    def get_degree(self, reg: str) -> int:
        """Get the degree of a node."""
        if reg in self.nodes:
            return self.nodes[reg].degree
        return 0

    def remove_node(self, reg: str):
        """Remove a node and all its edges from the graph."""
        if reg not in self.nodes:
            return
        node = self.nodes[reg]
        for neighbor_reg in list(node.neighbors):
            self.nodes[neighbor_reg].remove_neighbor(reg)
            edge = (min(reg, neighbor_reg), max(reg, neighbor_reg))
            self.edges.discard(edge)
        del self.nodes[reg]

    def get_num_edges(self) -> int:
        """Return the total number of interference edges."""
        return len(self.edges)

    def copy(self) -> 'InterferenceGraph':
        """Create a deep copy of the interference graph."""
        new_graph = InterferenceGraph()
        for reg, node in self.nodes.items():
            new_node = new_graph.add_node(reg)
            new_node.color = node.color
            new_node.is_precolored = node.is_precolored
            new_node.uses = node.uses
            new_node.is_spilled = node.is_spilled
            new_node.move_related = node.move_related
        for r1, r2 in self.edges:
            new_graph.add_edge(r1, r2)
        return new_graph


def count_register_uses(program: Program) -> Dict[str, int]:
    """Count the number of uses for each virtual register across the program."""
    use_counts = {}
    for block in program.blocks.values():
        for instr in block.instructions:
            for use in instr.uses:
                use_counts[use] = use_counts.get(use, 0) + 1
            for d in instr.defs:
                use_counts[d] = use_counts.get(d, 0) + 1
    return use_counts


def compute_spill_weights(graph: InterferenceGraph,
                          use_counts: Dict[str, int]) -> None:
    """Compute spill priority weights for all nodes.

    The weight determines how costly it is to spill a register.
    higher weight = less likely to spill (we spill minimum weight nodes).
    Weight should reflect: many uses = expensive to spill, high degree =
    beneficial to spill (frees many neighbors).

    Correct formula: weight = uses / degree (high uses = costly, high degree = cheap)
    """
    for reg, node in sorted(graph.nodes.items()):
        if node.is_precolored:
            node.spill_weight = float('inf')
            continue

        uses = use_counts.get(reg, 1)
        node.uses = uses

        # Compute spill weight: higher weight = less likely to spill
        # Weight reflects cost-to-benefit ratio of spilling this node
        # BUG: Using multiplication instead of division
        # This gives HIGH weight to nodes with high degree, making them
        # LESS likely to be spilled - exactly backwards from the intent
        node.spill_weight = uses * max(node.degree, 1)


def _compute_block_liveness(block: BasicBlock,
                            live_out_set: Set[str]) -> List[Set[str]]:
    """Compute per-instruction liveness within a block.

    Walk backward through instructions, computing the set of live registers
    at each program point. Returns list of live sets (one per instruction point).
    """
    # Start with live-out of the block
    current_live = set(live_out_set)
    # Collect live sets at each point (between instructions)
    live_points = [set(current_live)]

    for instr in reversed(block.instructions):
        # Before this instruction: remove defs, add uses
        current_live -= instr.defs
        current_live |= instr.uses
        live_points.append(set(current_live))

    live_points.reverse()
    return live_points


def build_interference_graph(
    program: Program,
    live_in: Dict[int, Set[str]],
    live_out: Dict[int, Set[str]],
    live_ranges: Dict[str, Set[int]],
    precolored_map: Dict[str, int]
) -> InterferenceGraph:
    """Build interference graph from liveness information.

    Two registers interfere if they are simultaneously live at any
    program point. We compute per-instruction liveness within each block
    to get precise interference.
    """
    graph = InterferenceGraph()

    # Add all registers as nodes
    all_regs = set(live_ranges.keys())
    for reg in sorted(all_regs):
        graph.add_node(reg)

    # Set up precolored nodes
    for reg, color in sorted(precolored_map.items()):
        if reg in graph.nodes:
            graph.nodes[reg].color = color
            graph.nodes[reg].is_precolored = True

    # Build edges using per-instruction liveness
    for bid in sorted(program.blocks.keys()):
        block = program.blocks[bid]
        live_points = _compute_block_liveness(block, live_out[bid])

        # At each program point, all live registers interfere
        for live_set in live_points:
            live_list = sorted(live_set)
            for i in range(len(live_list)):
                for j in range(i + 1, len(live_list)):
                    graph.add_edge(live_list[i], live_list[j])

    # Compute use counts and spill weights
    use_counts = count_register_uses(program)
    compute_spill_weights(graph, use_counts)

    return graph
