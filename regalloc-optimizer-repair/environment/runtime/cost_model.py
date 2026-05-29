# PLUTU-LUCKY-CANARY
"""
Pipeline Cost Model for instruction scheduling.
Computes latencies, detects hazards, estimates throughput,
and determines critical paths through dependency DAGs.
"""

from typing import Dict, List, Set, Tuple, Optional


# Default latency table (overridden by machine_spec at runtime)
DEFAULT_LATENCIES = {
    "load": 3,
    "store": 2,
    "add": 1,
    "sub": 1,
    "mul": 2,
    "div": 3,
    "mov": 1,
    "cmp": 1,
    "branch": 1,
    "call": 2,
    "ret": 1,
}


class HazardType:
    """Classification of pipeline hazards."""
    NONE = "none"
    RAW = "raw"          # Read After Write (true data dependency)
    WAR = "war"          # Write After Read (anti-dependency)
    WAW = "waw"          # Write After Write (output dependency)
    STRUCTURAL = "structural"  # Resource conflict


class DependencyEdge:
    """An edge in the dependency DAG between instructions."""

    def __init__(self, src_idx: int, dst_idx: int, hazard: str, latency: int):
        self.src_idx = src_idx
        self.dst_idx = dst_idx
        self.hazard = hazard
        self.latency = latency

    def __repr__(self):
        return f"DepEdge({self.src_idx}->{self.dst_idx}, {self.hazard}, lat={self.latency})"


class CostModel:
    """Pipeline cost model for scheduling decisions."""

    def __init__(self, latencies: Dict[str, int], pipeline_stages: int,
                 issue_width: int):
        self.latencies = latencies
        self.pipeline_stages = pipeline_stages
        self.issue_width = issue_width

    def get_latency(self, op: str) -> int:
        """Get the execution latency for an operation."""
        return self.latencies.get(op, 1)

    def classify_hazard(self, earlier_defs: Set[str], earlier_uses: Set[str],
                        later_defs: Set[str], later_uses: Set[str]) -> str:
        """Classify the hazard between two instructions.

        RAW: earlier writes, later reads (flow dependency)
        WAR: earlier reads, later writes (anti-dependency)
        WAW: earlier writes, later writes (output dependency)
        """
        # RAW: true data dependency - later reads what earlier writes
        if earlier_defs & later_uses:
            return HazardType.RAW

        # WAR: anti-dependency - later writes what earlier reads
        if earlier_uses & later_defs:
            return HazardType.WAR

        # WAW: output dependency - both write same register
        if earlier_defs & later_defs:
            return HazardType.WAW

        return HazardType.NONE

    def compute_stall_cycles(self, producer_op: str, consumer_op: str,
                             distance: int) -> int:
        """Compute stall cycles between producer and consumer.

        A stall occurs when the consumer needs data before the producer
        has completed execution. Stall = latency - distance.
        """
        latency = self.get_latency(producer_op)
        stall = latency - distance
        return max(0, stall)

    def check_structural_hazard(self, ops_in_cycle: List[str]) -> bool:
        """Check if too many instructions are issued in one cycle.

        A structural hazard occurs when more instructions need the same
        functional unit than available in one cycle.
        """
        if len(ops_in_cycle) > self.issue_width:
            return True

        # Memory operations share a port
        mem_ops = sum(1 for op in ops_in_cycle if op in ("load", "store"))
        if mem_ops > 1:
            return True

        # Multiply/divide share a unit
        complex_ops = sum(1 for op in ops_in_cycle if op in ("mul", "div"))
        if complex_ops > 1:
            return True

        return False

    def build_dependency_dag(self, instructions: List) -> List[DependencyEdge]:
        """Build a dependency DAG for a sequence of instructions.

        Returns edges representing all data dependencies between instructions.
        """
        edges = []

        for i in range(len(instructions)):
            for j in range(i + 1, len(instructions)):
                instr_i = instructions[i]
                instr_j = instructions[j]

                hazard = self.classify_hazard(
                    instr_i.defs, instr_i.uses,
                    instr_j.defs, instr_j.uses
                )

                if hazard != HazardType.NONE:
                    if hazard == HazardType.RAW:
                        lat = self.get_latency(instr_i.op)
                    elif hazard == HazardType.WAR:
                        lat = 1  # Anti-deps have minimum latency
                    else:  # WAW
                        lat = self.get_latency(instr_i.op)

                    edges.append(DependencyEdge(i, j, hazard, lat))

        return edges

    def compute_critical_path(self, num_instructions: int,
                              edges: List[DependencyEdge]) -> int:
        """Compute the critical path length through the dependency DAG.

        Uses longest-path algorithm (topological order is implicit
        since edges always go from lower to higher index).
        """
        # Distance from start to each node
        dist = [0] * num_instructions

        for edge in sorted(edges, key=lambda e: e.src_idx):
            new_dist = dist[edge.src_idx] + edge.latency
            if new_dist > dist[edge.dst_idx]:
                dist[edge.dst_idx] = new_dist

        return max(dist) if dist else 0

    def estimate_throughput(self, instructions: List,
                            edges: List[DependencyEdge]) -> float:
        """Estimate IPC (instructions per cycle) for a schedule.

        Throughput = num_instructions / (critical_path + pipeline_drain).
        """
        n = len(instructions)
        if n == 0:
            return 0.0

        cp = self.compute_critical_path(n, edges)
        total_cycles = cp + self.pipeline_stages
        return n / max(total_cycles, 1)

    def compute_schedule_cost(self, schedule_order: List[int],
                              instructions: List) -> int:
        """Compute total stall cycles for a given instruction ordering.

        Walks through the schedule and counts pipeline stalls caused
        by data dependencies that cannot be hidden.
        """
        total_stalls = 0
        # Map from register to (defining instruction index in schedule, op)
        last_def = {}

        for pos, instr_idx in enumerate(schedule_order):
            instr = instructions[instr_idx]

            for use_reg in sorted(instr.uses):
                if use_reg in last_def:
                    def_pos, def_op = last_def[use_reg]
                    distance = pos - def_pos
                    stall = self.compute_stall_cycles(def_op, instr.op, distance)
                    total_stalls += stall

            for def_reg in sorted(instr.defs):
                last_def[def_reg] = (pos, instr.op)

        return total_stalls


def create_cost_model(machine_spec: dict) -> CostModel:
    """Factory function to create a CostModel from machine specification."""
    latencies = machine_spec.get("latencies", DEFAULT_LATENCIES)
    stages = machine_spec.get("pipeline_stages", 3)
    width = machine_spec.get("issue_width", 2)
    return CostModel(latencies, stages, width)
