# PLUTU-LUCKY-CANARY
"""
IR Utilities for bytecode manipulation.
Provides instruction creation helpers, basic block representation,
def/use extraction, dominance computation, and loop detection.
"""

from typing import Dict, List, Set, Tuple, Optional


class Instruction:
    """Represents a single bytecode instruction."""

    def __init__(self, op: str, defs: List[str], uses: List[str],
                 imm: Optional[int] = None, precolored_def: Optional[str] = None):
        self.op = op
        self.defs = set(defs)
        self.uses = set(uses)
        self.imm = imm
        self.precolored_def = precolored_def
        self.block_id = -1
        self.index = -1

    def is_move(self) -> bool:
        """Check if this is a register-to-register move."""
        return self.op == "mov" and len(self.uses) == 1 and len(self.defs) == 1

    def is_branch(self) -> bool:
        """Check if this is a control flow instruction."""
        return self.op in ("branch", "ret", "call")

    def is_memory(self) -> bool:
        """Check if this accesses memory."""
        return self.op in ("load", "store")

    def get_single_def(self) -> Optional[str]:
        """Return the single defined register, or None."""
        if len(self.defs) == 1:
            return next(iter(self.defs))
        return None

    def get_single_use(self) -> Optional[str]:
        """Return the single used register, or None (for moves)."""
        if len(self.uses) == 1:
            return next(iter(self.uses))
        return None

    def __repr__(self):
        parts = [self.op]
        if self.defs:
            parts.append(f"def={sorted(self.defs)}")
        if self.uses:
            parts.append(f"use={sorted(self.uses)}")
        if self.imm is not None:
            parts.append(f"imm={self.imm}")
        return f"Instr({', '.join(parts)})"


class BasicBlock:
    """Represents a basic block in the control flow graph."""

    def __init__(self, block_id: int):
        self.id = block_id
        self.instructions: List[Instruction] = []
        self.successors: List[int] = []
        self.predecessors: List[int] = []

    def add_instruction(self, instr: Instruction):
        """Append an instruction to this block."""
        instr.block_id = self.id
        instr.index = len(self.instructions)
        self.instructions.append(instr)

    def get_defs(self) -> Set[str]:
        """Get all registers defined in this block."""
        defs = set()
        for instr in self.instructions:
            defs.update(instr.defs)
        return defs

    def get_uses(self) -> Set[str]:
        """Get all registers used in this block."""
        uses = set()
        for instr in self.instructions:
            uses.update(instr.uses)
        return uses

    def __repr__(self):
        return f"BB{self.id}(instrs={len(self.instructions)}, succ={self.successors})"


class PhiNode:
    """Represents a PHI function at a block boundary."""

    def __init__(self, block_id: int, def_reg: str,
                 operands: List[Tuple[str, int]]):
        self.block_id = block_id
        self.def_reg = def_reg
        # List of (value_register, from_block_id)
        self.operands = operands

    def get_operand_for_pred(self, pred_id: int) -> Optional[str]:
        """Get the operand value coming from a specific predecessor."""
        for val, from_block in self.operands:
            if from_block == pred_id:
                return val
        return None

    def __repr__(self):
        ops = ", ".join(f"{v} from B{b}" for v, b in self.operands)
        return f"PHI(B{self.block_id}: {self.def_reg} = [{ops}])"


class Program:
    """Represents a complete program with blocks and PHI nodes."""

    def __init__(self, name: str):
        self.name = name
        self.blocks: Dict[int, BasicBlock] = {}
        self.phi_nodes: List[PhiNode] = []

    def add_block(self, block: BasicBlock):
        """Add a basic block to the program."""
        self.blocks[block.id] = block

    def add_phi(self, phi: PhiNode):
        """Add a PHI node."""
        self.phi_nodes.append(phi)

    def get_all_registers(self) -> Set[str]:
        """Get all virtual registers referenced in the program."""
        regs = set()
        for block in self.blocks.values():
            regs.update(block.get_defs())
            regs.update(block.get_uses())
        for phi in self.phi_nodes:
            regs.add(phi.def_reg)
            for val, _ in phi.operands:
                regs.add(val)
        return regs

    def get_block_order(self) -> List[int]:
        """Return blocks in reverse postorder for iteration."""
        visited = set()
        order = []

        def dfs(bid):
            if bid in visited:
                return
            visited.add(bid)
            block = self.blocks[bid]
            for succ in block.successors:
                dfs(succ)
            order.append(bid)

        dfs(0)
        order.reverse()
        return order


def extract_defs(instr_data: dict) -> Set[str]:
    """Extract defined registers from raw instruction data."""
    return set(instr_data.get("def", []))


def extract_uses(instr_data: dict) -> Set[str]:
    """Extract used registers from raw instruction data."""
    return set(instr_data.get("use", []))


def compute_dominators(blocks: Dict[int, BasicBlock]) -> Dict[int, Set[int]]:
    """Compute dominator sets using iterative dataflow algorithm."""
    all_ids = set(blocks.keys())
    dom = {}

    # Entry block dominates only itself
    entry_id = 0
    dom[entry_id] = {entry_id}

    # All other blocks: initialize to all blocks
    for bid in all_ids:
        if bid != entry_id:
            dom[bid] = set(all_ids)

    # Iterate until convergence
    changed = True
    while changed:
        changed = False
        for bid in sorted(all_ids):
            if bid == entry_id:
                continue
            preds = blocks[bid].predecessors
            if not preds:
                new_dom = {bid}
            else:
                new_dom = set(all_ids)
                for p in preds:
                    new_dom = new_dom & dom[p]
                new_dom.add(bid)
            if new_dom != dom[bid]:
                dom[bid] = new_dom
                changed = True

    return dom


def find_back_edges(blocks: Dict[int, BasicBlock],
                    dom: Dict[int, Set[int]]) -> List[Tuple[int, int]]:
    """Find back edges in the CFG (edges where target dominates source)."""
    back_edges = []
    for bid, block in sorted(blocks.items()):
        for succ in block.successors:
            if succ in dom.get(bid, set()):
                back_edges.append((bid, succ))
    return back_edges


def detect_loops(blocks: Dict[int, BasicBlock]) -> List[Tuple[int, Set[int]]]:
    """Detect natural loops via back edge analysis.
    Returns list of (header_block_id, set_of_loop_body_block_ids)."""
    dom = compute_dominators(blocks)
    back_edges = find_back_edges(blocks, dom)

    loops = []
    for tail, header in back_edges:
        # Natural loop: all blocks that can reach tail without going through header
        loop_body = {header, tail}
        worklist = [tail]
        while worklist:
            node = worklist.pop()
            for pred in blocks[node].predecessors:
                if pred not in loop_body:
                    loop_body.add(pred)
                    worklist.append(pred)
        loops.append((header, loop_body))

    return loops


def build_program_from_json(data: dict) -> Program:
    """Construct a Program from JSON representation."""
    prog = Program(data["name"])

    for block_data in data["blocks"]:
        block = BasicBlock(block_data["id"])
        block.successors = block_data.get("successors", [])
        block.predecessors = block_data.get("predecessors", [])

        for instr_data in block_data["instructions"]:
            instr = Instruction(
                op=instr_data["op"],
                defs=instr_data.get("def", []),
                uses=instr_data.get("use", []),
                imm=instr_data.get("imm"),
                precolored_def=instr_data.get("precolored_def")
            )
            block.add_instruction(instr)

        prog.add_block(block)

    for phi_data in data.get("phi_nodes", []):
        operands = [(op["value"], op["from_block"]) for op in phi_data["operands"]]
        phi = PhiNode(phi_data["block"], phi_data["def"], operands)
        prog.add_phi(phi)

    return prog
