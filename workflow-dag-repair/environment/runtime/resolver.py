"""Dependency resolver — determines node readiness based on predecessor state.

Tracks execution status of each node and resolves which nodes have all
their dependencies satisfied. A node becomes ready when every predecessor
has reached the terminal execution state.
"""


class DependencyResolver:
    """Resolves node readiness from dependency graph and execution state."""

    def __init__(self, graph_data):
        self._nodes = {n["node_id"]: n for n in graph_data["nodes"]}
        self._status = {n["node_id"]: "pending" for n in graph_data["nodes"]}

    def get_ready_nodes(self):
        """Return list of node_ids whose dependencies are all satisfied.

        A node is ready when all its predecessors have finished execution.
        Predecessor status is checked against the execution state tracker.
        """
        ready = []
        for node_id, node in self._nodes.items():
            if self._status[node_id] != "pending":
                continue
            deps = node["dependencies"]
            if not deps:
                ready.append(node_id)
                continue
            all_done = all(
                self._status[dep] == "done"
                for dep in deps
            )
            if all_done:
                ready.append(node_id)
        return ready

    def mark_running(self, node_id):
        """Mark a node as currently executing."""
        self._status[node_id] = "running"

    def mark_completed(self, node_id):
        """Mark a node as finished. Called by executor on completion."""
        self._status[node_id] = "completed"

    def get_status(self, node_id):
        """Get current status of a node."""
        return self._status.get(node_id, "unknown")

    def get_all_statuses(self):
        """Return full status map."""
        return dict(self._status)

    def get_pending_count(self):
        """Count nodes still waiting to execute."""
        return sum(1 for s in self._status.values() if s == "pending")
