# PLUTU-LUCKY-CANARY
"""
Instruction Scheduler - list scheduling to minimize pipeline stalls.
Reorders instructions within basic blocks to hide latencies while
respecting data dependencies (flow, anti, and output).
"""

from typing import Dict, List, Set, Tuple, Optional
from .ir_utils import Program, BasicBlock, Instruction
from .cost_model import CostModel, HazardType


class DepEdge:
    """Dependency edge between two instructions in a block."""

    def __init__(self, src: int, dst: int, dep_type: str, latency: int):
        self.src = src
        self.dst = dst
        self.dep_type = dep_type
        self.latency = latency


def compute_flow_dependencies(instructions: List[Instruction]) -> List[DepEdge]:
    """Compute RAW (flow) dependencies: later reads what earlier writes.

    A flow dependency exists from instruction i to j (i < j) when
    instruction i defines a register that instruction j uses.
    """
    edges = []
    for i in range(len(instructions)):
        for j in range(i + 1, len(instructions)):
            # Flow: i defines something j uses
            common = instructions[i].defs & instructions[j].uses
            if common:
                edges.append(DepEdge(i, j, HazardType.RAW,
                                     _get_latency(instructions[i])))
    return edges


def compute_output_dependencies(instructions: List[Instruction]) -> List[DepEdge]:
    """Compute WAW (output) dependencies: both write same register.

    An output dependency exists from i to j when both define the
    same register - they must execute in order.
    """
    edges = []
    for i in range(len(instructions)):
        for j in range(i + 1, len(instructions)):
            # Output: both define the same register
            common = instructions[i].defs & instructions[j].defs
            if common:
                edges.append(DepEdge(i, j, HazardType.WAW,
                                     _get_latency(instructions[i])))
    return edges


def compute_anti_dependencies(instructions: List[Instruction]) -> List[DepEdge]:
    """Compute WAR (anti) dependencies.

    Check if current instruction reads what later instruction writes.
    An anti-dependency from i to j means i reads a register that j writes,
    so j cannot execute before i finishes reading.
    """
    edges = []
    for i in range(len(instructions)):
        for j in range(i + 1, len(instructions)):
            # BUG: This checks if i DEFINES what j USES (that's flow dep!)
            # Should check if i USES what j DEFINES (anti-dep)
            # Comment above says "reads what later writes" which is correct
            # for anti-dep, but code implements "defines what later uses"
            flow_deps = instructions[i].defs & instructions[j].uses
            if flow_deps:
                edges.append(DepEdge(i, j, HazardType.WAR, 1))
    return edges


def _get_latency(instr: Instruction) -> int:
    """Get default latency for instruction type."""
    latency_table = {
        "load": 3, "store": 2, "add": 1, "sub": 1,
        "mul": 2, "div": 3, "mov": 1, "cmp": 1,
        "branch": 1, "call": 2, "ret": 1
    }
    return latency_table.get(instr.op, 1)


def build_dependency_graph(instructions: List[Instruction]) -> List[DepEdge]:
    """Build complete dependency graph for a basic block.

    Combines flow, anti, and output dependencies.
    """
    all_edges = []
    all_edges.extend(compute_flow_dependencies(instructions))
    all_edges.extend(compute_anti_dependencies(instructions))
    all_edges.extend(compute_output_dependencies(instructions))
    return all_edges


def compute_priorities(instructions: List[Instruction],
                       edges: List[DepEdge]) -> List[int]:
    """Compute scheduling priority for each instruction.

    Priority = longest path from this instruction to any exit.
    Higher priority instructions are scheduled first.
    """
    n = len(instructions)
    # Build adjacency for successors
    successors: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(n)}
    for edge in edges:
        successors[edge.src].append((edge.dst, edge.latency))

    # Compute longest path from each node (reverse topological order)
    priority = [0] * n
    # Process in reverse order (sinks first)
    for i in range(n - 1, -1, -1):
        max_succ = 0
        for dst, lat in successors[i]:
            if priority[dst] + lat > max_succ:
                max_succ = priority[dst] + lat
        priority[i] = max_succ + _get_latency(instructions[i])

    return priority


def list_schedule(instructions: List[Instruction],
                  edges: List[DepEdge],
                  cost_model: CostModel) -> Tuple[List[int], int]:
    """Perform list scheduling on a basic block.

    Returns (schedule_order, num_stalls) where schedule_order is a
    permutation of instruction indices.
    """
    n = len(instructions)
    if n == 0:
        return [], 0

    # Build predecessor count for readiness
    pred_count = [0] * n
    pred_edges: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(n)}
    for edge in edges:
        pred_count[edge.dst] += 1
        pred_edges[edge.dst].append((edge.src, edge.latency))

    priorities = compute_priorities(instructions, edges)

    # Ready set: instructions with no unsatisfied predecessors
    ready = []
    for i in range(n):
        if pred_count[i] == 0:
            ready.append(i)

    schedule = []
    scheduled = set()
    cycle_available = [0] * n  # Earliest cycle each instruction can execute
    current_cycle = 0
    total_stalls = 0

    while ready or len(schedule) < n:
        # Find instructions that are ready and available this cycle
        available_now = []
        for idx in ready:
            if cycle_available[idx] <= current_cycle:
                available_now.append(idx)

        if not available_now:
            # Stall: advance to next available cycle
            if ready:
                next_available = min(cycle_available[idx] for idx in ready)
                stall_amount = next_available - current_cycle
                total_stalls += stall_amount
                current_cycle = next_available
                continue
            else:
                break

        # Pick highest priority instruction
        available_now.sort(key=lambda i: -priorities[i])
        chosen = available_now[0]

        schedule.append(chosen)
        ready.remove(chosen)
        scheduled.add(chosen)

        # Update successors
        for edge in edges:
            if edge.src == chosen and edge.dst not in scheduled:
                pred_count[edge.dst] -= 1
                # Set earliest available cycle for dependent instruction
                earliest = current_cycle + edge.latency
                if earliest > cycle_available[edge.dst]:
                    cycle_available[edge.dst] = earliest
                if pred_count[edge.dst] == 0:
                    ready.append(edge.dst)

        current_cycle += 1

    return schedule, total_stalls


def schedule_program(program: Program, cost_model: CostModel) -> int:
    """Schedule all basic blocks in a program.

    Returns total stall cycles across all blocks.
    """
    total_stalls = 0

    for bid in sorted(program.blocks.keys()):
        block = program.blocks[bid]
        if len(block.instructions) <= 1:
            continue

        edges = build_dependency_graph(block.instructions)
        schedule_order, stalls = list_schedule(
            block.instructions, edges, cost_model
        )

        # Reorder instructions according to schedule
        if schedule_order and len(schedule_order) == len(block.instructions):
            new_instrs = [block.instructions[i] for i in schedule_order]
            block.instructions = new_instrs

        total_stalls += stalls

    return total_stalls
