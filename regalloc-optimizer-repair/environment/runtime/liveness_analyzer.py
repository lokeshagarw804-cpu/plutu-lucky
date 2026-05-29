# PLUTU-LUCKY-CANARY
"""
Liveness Analyzer - Backward dataflow analysis for register liveness.
Computes live-in and live-out sets for each basic block using a worklist
algorithm. Handles PHI nodes at block boundaries by propagating operands
to corresponding predecessor blocks.
"""

from typing import Dict, List, Set, Tuple
from .ir_utils import Program, BasicBlock, PhiNode, Instruction


def compute_gen_kill(block: BasicBlock) -> Tuple[Set[str], Set[str]]:
    """Compute GEN and KILL sets for a basic block.

    GEN: registers used before being defined in the block
    KILL: registers defined in the block
    """
    gen = set()
    kill = set()

    # Process instructions in forward order for correct gen/kill
    for instr in block.instructions:
        # Uses that haven't been killed yet are generated
        for use in sorted(instr.uses):
            if use not in kill:
                gen.add(use)
        # Definitions kill the register
        for d in sorted(instr.defs):
            kill.add(d)

    return gen, kill


def initialize_liveness_sets(program: Program) -> Tuple[
    Dict[int, Set[str]], Dict[int, Set[str]]
]:
    """Initialize live-in and live-out sets to empty for all blocks."""
    live_in = {}
    live_out = {}
    for bid in program.blocks:
        live_in[bid] = set()
        live_out[bid] = set()
    return live_in, live_out


def propagate_phi_liveness(program: Program,
                           live_in: Dict[int, Set[str]],
                           live_out: Dict[int, Set[str]]) -> None:
    """Propagate liveness information for PHI node operands.

    For each PHI node, add operand to live-out of corresponding predecessor.
    The PHI definition is added to the live-in of the block containing it.
    """
    for phi in program.phi_nodes:
        block = program.blocks[phi.block_id]
        predecessors = block.predecessors

        # PHI def is live-in at the block (it defines a value used later)
        # But we don't add it to live-in directly - the GEN/KILL handles it

        # BUG: For each operand, we should add it to the live-out of ONLY
        # the specific predecessor it comes from. Instead, this code adds
        # each operand to ALL predecessor blocks' live-out sets.
        # The comment says "add operand to live-out of corresponding predecessor"
        # but the implementation over-approximates by using all predecessors.
        for operand_val, from_block in phi.operands:
            # add operand to live-out of corresponding predecessor
            for pred_id in predecessors:
                live_out[pred_id].add(operand_val)


def worklist_iterate(program: Program,
                     gen_kill: Dict[int, Tuple[Set[str], Set[str]]],
                     live_in: Dict[int, Set[str]],
                     live_out: Dict[int, Set[str]]) -> int:
    """Run worklist-based backward dataflow iteration.

    Returns number of iterations until convergence.
    Liveness equations:
        live_out[B] = union(live_in[S]) for all successors S of B
        live_in[B] = gen[B] | (live_out[B] - kill[B])
    """
    # Worklist initialization: all blocks in reverse order
    block_order = sorted(program.blocks.keys(), reverse=True)
    worklist = list(block_order)
    in_worklist = set(worklist)
    iterations = 0

    while worklist:
        bid = worklist.pop(0)
        in_worklist.discard(bid)
        iterations += 1

        block = program.blocks[bid]
        gen, kill = gen_kill[bid]

        # Compute live-out as union of successors' live-in
        new_live_out = set()
        for succ_id in block.successors:
            new_live_out |= live_in[succ_id]

        # Include any PHI-propagated values already in live_out
        new_live_out |= live_out[bid]

        # Compute live-in from transfer function
        new_live_in = gen | (new_live_out - kill)

        # Check for changes
        changed = (new_live_in != live_in[bid] or
                   new_live_out != live_out[bid])

        if changed:
            live_in[bid] = new_live_in
            live_out[bid] = new_live_out

            # Add predecessors to worklist
            for pred_id in block.predecessors:
                if pred_id not in in_worklist:
                    worklist.append(pred_id)
                    in_worklist.add(pred_id)

    return iterations


def compute_live_ranges(program: Program,
                        live_in: Dict[int, Set[str]],
                        live_out: Dict[int, Set[str]]
                        ) -> Dict[str, Set[int]]:
    """Compute live ranges: for each register, which blocks it is live in.

    A register is live in a block if it is in live-in OR live-out of that block,
    or if it is defined and used within the block.
    """
    live_ranges = {}

    for bid, block in sorted(program.blocks.items()):
        # Registers live at entry or exit
        live_at_block = live_in[bid] | live_out[bid]

        # Registers defined and later used within same block
        for instr in block.instructions:
            for d in instr.defs:
                live_at_block.add(d)

        for reg in live_at_block:
            if reg not in live_ranges:
                live_ranges[reg] = set()
            live_ranges[reg].add(bid)

    return live_ranges


def analyze_liveness(program: Program) -> Tuple[
    Dict[int, Set[str]], Dict[int, Set[str]], Dict[str, Set[int]]
]:
    """Main entry point: compute liveness for all blocks.

    Returns:
        live_in: mapping from block id to set of live-in registers
        live_out: mapping from block id to set of live-out registers
        live_ranges: mapping from register to set of blocks it's live in
    """
    # Step 1: Initialize
    live_in, live_out = initialize_liveness_sets(program)

    # Step 2: Compute gen/kill for each block
    gen_kill = {}
    for bid, block in sorted(program.blocks.items()):
        gen_kill[bid] = compute_gen_kill(block)

    # Step 3: Propagate PHI node liveness
    propagate_phi_liveness(program, live_in, live_out)

    # Step 4: Worklist iteration until convergence
    worklist_iterate(program, gen_kill, live_in, live_out)

    # Step 5: Compute live ranges from converged sets
    live_ranges = compute_live_ranges(program, live_in, live_out)

    return live_in, live_out, live_ranges
