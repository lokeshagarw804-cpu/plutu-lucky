# PLUTU-LUCKY-CANARY
"""
Spill Manager - handles register spilling when graph coloring fails.
Inserts store instructions after definitions and load instructions
before uses for spilled registers. Updates the interference graph
after spilling.
"""

from typing import Dict, List, Set, Tuple
from .ir_utils import Program, BasicBlock, Instruction
from .interference_graph import InterferenceGraph, IGNode


class SpillSlot:
    """Represents a stack slot for a spilled register."""

    def __init__(self, reg: str, slot_id: int):
        self.reg = reg
        self.slot_id = slot_id
        self.offset = slot_id * 8  # 8 bytes per slot

    def __repr__(self):
        return f"SpillSlot({self.reg}, slot={self.slot_id}, off={self.offset})"


def select_spill_candidates(graph: InterferenceGraph,
                            spilled: List[str]) -> List[str]:
    """Select registers to spill based on minimum weight.

    From the list of potential spills, choose those with lowest weight.
    """
    candidates = []
    for reg in sorted(spilled):
        if reg in graph.nodes:
            candidates.append(reg)
    # Sort by spill weight (ascending - spill cheapest first)
    candidates.sort(key=lambda r: graph.nodes[r].spill_weight)
    return candidates


def insert_spill_stores(program: Program, reg: str,
                        slot: SpillSlot) -> int:
    """Insert store instructions after each definition of the spilled register.

    Returns the number of stores inserted.
    """
    stores_inserted = 0
    for block in program.blocks.values():
        new_instructions = []
        for instr in block.instructions:
            new_instructions.append(instr)
            if reg in instr.defs:
                # Insert store after definition
                store_instr = Instruction(
                    op="store",
                    defs=[],
                    uses=[reg],
                    imm=slot.offset
                )
                store_instr.block_id = block.id
                new_instructions.append(store_instr)
                stores_inserted += 1
        block.instructions = new_instructions
    return stores_inserted


def insert_spill_loads(program: Program, reg: str,
                       slot: SpillSlot) -> int:
    """Insert load instructions before each use of the spilled register.

    Creates a fresh temporary for each load to avoid long live ranges.
    Returns the number of loads inserted.
    """
    loads_inserted = 0
    for block in program.blocks.values():
        new_instructions = []
        for instr in block.instructions:
            if reg in instr.uses and reg not in instr.defs:
                # Insert load before use
                load_instr = Instruction(
                    op="load",
                    defs=[reg],
                    uses=[],
                    imm=slot.offset
                )
                load_instr.block_id = block.id
                new_instructions.append(load_instr)
                loads_inserted += 1
            new_instructions.append(instr)
        block.instructions = new_instructions
    return loads_inserted


def update_graph_after_spill(graph: InterferenceGraph,
                             reg: str) -> None:
    """Update interference graph after spilling a register.

    Remove the spilled register's node and all its edges.
    This reduces pressure for remaining allocation.
    """
    if reg in graph.nodes:
        graph.nodes[reg].is_spilled = True
        graph.remove_node(reg)


def handle_spills(program: Program, graph: InterferenceGraph,
                  spilled_regs: List[str]) -> int:
    """Main spill handling routine.

    For each spilled register:
    1. Assign a spill slot
    2. Insert stores after definitions
    3. Insert loads before uses
    4. Update the interference graph

    Returns total spill instructions inserted.
    """
    total_inserted = 0
    candidates = select_spill_candidates(graph, spilled_regs)

    for idx, reg in enumerate(candidates):
        slot = SpillSlot(reg, idx)

        stores = insert_spill_stores(program, reg, slot)
        loads = insert_spill_loads(program, reg, slot)
        total_inserted += stores + loads

        update_graph_after_spill(graph, reg)

    return total_inserted
