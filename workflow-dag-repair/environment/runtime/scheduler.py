"""Execution scheduler — assigns nodes to time-slots respecting constraints.

Builds a multi-slot execution schedule where each slot contains nodes
that can run concurrently, limited by max_parallelism from the constrained
scheduler configuration. Nodes are assigned to the earliest available slot
once their dependencies are resolved.
"""
import configparser


class ExecutionScheduler:
    """Schedules DAG nodes into time-slots with parallelism constraints."""

    def __init__(self, config_path, resolver, prioritizer, graph_data):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._max_parallel = self._config.getint("scheduler", "max_parallelism")
        self._resolver = resolver
        self._prioritizer = prioritizer
        self._nodes = {n["node_id"]: n for n in graph_data["nodes"]}
        self._schedule = []

    def build_schedule(self):
        """Build execution schedule by assigning nodes to time-slots.

        Each iteration:
        1. Get ready nodes (all deps satisfied)
        2. Rank by priority
        3. Assign top-N to current slot (N = max_parallelism)
        4. Mark assigned nodes as running then completed
        5. Repeat until all nodes scheduled

        Returns list of slots, each containing list of scheduled node_ids.
        """
        total_nodes = len(self._nodes)
        scheduled_count = 0
        max_iterations = total_nodes + 5  # safety bound

        iteration = 0
        while scheduled_count < total_nodes and iteration < max_iterations:
            iteration += 1
            ready = self._resolver.get_ready_nodes()
            if not ready:
                break

            ranked = self._prioritizer.rank_nodes(ready)
            slot = ranked[:self._max_parallel]

            for node_id in slot:
                self._resolver.mark_running(node_id)

            for node_id in slot:
                self._resolver.mark_completed(node_id)

            self._schedule.append(slot)
            scheduled_count += len(slot)

        return self._schedule

    def get_schedule(self):
        """Return the built schedule."""
        return self._schedule

    def get_slot_count(self):
        """Return total number of time-slots."""
        return len(self._schedule)

    def get_max_parallelism(self):
        """Return configured max parallelism."""
        return self._max_parallel
