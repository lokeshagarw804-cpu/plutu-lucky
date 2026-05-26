#!/usr/bin/env python3
"""Repair script for packet route analyzer.

Patches defects in runtime source files and re-runs the system.
"""
import sys


def patch_router():
    """Fix Dijkstra relaxation condition.

    The stability damping check requires a new path to improve by
    min_hop_cost over the current best. This is incorrect — standard
    Dijkstra relaxation should accept any strictly shorter path.
    """
    path = "/app/runtime/router.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "if new_cost < dist[neighbor] - self._min_hop_cost:",
        "if new_cost < dist[neighbor]:"
    )

    with open(path, "w") as f:
        f.write(content)



def patch_tracker():
    """Fix loop detection path history.

    The _check_hop method overwrites path_history with a new set
    containing only the current hop pair, losing all previously visited
    nodes. Must add current_node to the existing set instead.
    """
    path = "/app/runtime/tracker.py"
    with open(path, "r") as f:
        content = f.read()

    old_check_hop = '''    def _check_hop(self, packet_id, current_node, next_node):
        """Check a single hop for loop condition.

        Creates a per-hop visited snapshot and checks whether the
        next node has already been traversed in this packet's path.
        Adds current node to the running path set after checking.
        """
        visited = set()
        visited.add(current_node)
        visited.add(next_node)
        if next_node in self._path_history[packet_id]:
            return True
        self._path_history[packet_id] = visited
        return False'''

    new_check_hop = '''    def _check_hop(self, packet_id, current_node, next_node):
        """Check a single hop for loop condition.

        Creates a per-hop visited snapshot and checks whether the
        next node has already been traversed in this packet's path.
        Adds current node to the running path set after checking.
        """
        self._path_history[packet_id].add(current_node)
        if next_node in self._path_history[packet_id]:
            return True
        return False'''

    content = content.replace(old_check_hop, new_check_hop)

    with open(path, "w") as f:
        f.write(content)



def patch_reporter():
    """Fix cost accumulator and sort key.

    1. source_totals overwrites with each flow's path_cost instead of
       accumulating across all destinations for that source.
    2. Sort key groups by source_node first instead of sorting globally
       by descending anomaly_score with source and dest as tiebreakers.
    """
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix accumulation (= should be +=)
    content = content.replace(
        "source_totals[src] = total_cost",
        "source_totals[src] = source_totals.get(src, 0) + flow[\"path_cost\"]"
    )

    # Remove the now-redundant total_cost assignment
    content = content.replace(
        "            total_cost = flow[\"path_cost\"]\n",
        ""
    )

    # Fix sort key
    content = content.replace(
        'flows.sort(key=lambda f: (f["source_node"], -f["anomaly_score"]))',
        'flows.sort(key=lambda f: (-f["anomaly_score"], f["source_node"], f["dest_node"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_router()
    patch_tracker()
    patch_reporter()

    import subprocess
    result = subprocess.run(
        ["python3", "-m", "runtime.main"],
        cwd="/app",
        capture_output=True
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
