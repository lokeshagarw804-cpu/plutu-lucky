"""Priority calculator — computes effective scheduling priority for nodes.

Calculates each node's effective priority considering:
- Base priority from workflow definition (mapped to numeric weight)
- Critical path cost (longest dependency chain cost to reach this node)
- Priority boost overrides for specific nodes
- Depth-based decay factor

The critical path cost represents the minimum time before this node
can start, considering all predecessor chains. For nodes with multiple
predecessors, the critical path is the maximum cost among all
incoming dependency chains (the bottleneck path).
"""


class PriorityCalculator:
    """Computes effective scheduling priority for workflow nodes."""

    def __init__(self, graph_data, priority_weights, overrides):
        self._nodes = {n["node_id"]: n for n in graph_data["nodes"]}
        self._weights = priority_weights
        self._overrides = {o["node_id"]: o for o in overrides["overrides"]}
        self._decay = overrides.get("decay_per_depth", 0.1)
        self._depths = {}
        self._critical_costs = {}
        self._compute_depths()
        self._compute_critical_path_costs()

    def _compute_depths(self):
        """Compute topological depth for each node (longest path from root)."""
        for node_id in self._nodes:
            self._depths[node_id] = self._get_depth(node_id)

    def _get_depth(self, node_id):
        """Recursively compute depth."""
        if node_id in self._depths:
            return self._depths[node_id]
        deps = self._nodes[node_id]["dependencies"]
        if not deps:
            return 0
        return 1 + max(self._get_depth(d) for d in deps)

    def _compute_critical_path_costs(self):
        """Compute critical path cost for each node.

        The critical path cost to a node is the cost along the longest
        weighted predecessor chain. For a node with multiple predecessors,
        we take each predecessor's critical cost plus its own execution
        cost, and combine them.
        """
        for node_id in self._nodes:
            self._critical_costs[node_id] = self._get_critical_cost(node_id)

    def _get_critical_cost(self, node_id):
        """Compute critical path cost recursively."""
        if node_id in self._critical_costs:
            return self._critical_costs[node_id]
        deps = self._nodes[node_id]["dependencies"]
        if not deps:
            return 0
        # Accumulate cost from all predecessor chains
        total = 0
        for dep in deps:
            dep_cost = self._get_critical_cost(dep) + self._nodes[dep]["cost"]
            total += dep_cost
        return total

    def get_effective_priority(self, node_id):
        """Compute final scheduling priority for a node.

        Priority formula:
          base_weight * boost_factor - (depth * decay) + critical_cost_factor

        Higher values are scheduled earlier.
        """
        node = self._nodes[node_id]
        priority_level = node["priority"]
        base_weight = self._weights.get(priority_level,
                                        self._weights.get("medium", 2))
        depth = self._depths[node_id]
        critical_cost = self._critical_costs[node_id]

        boost = 1.0
        if node_id in self._overrides:
            boost = self._overrides[node_id]["boost_factor"]

        effective = (base_weight * boost) - (depth * self._decay) + (critical_cost * 0.1)
        return round(effective, 3)

    def get_depth(self, node_id):
        """Return computed depth for a node."""
        return self._depths.get(node_id, 0)

    def get_critical_cost(self, node_id):
        """Return computed critical path cost."""
        return self._critical_costs.get(node_id, 0)

    def rank_nodes(self, node_ids):
        """Sort nodes by effective priority descending, then by node_id.

        Ties in priority are broken by node_id for deterministic scheduling.
        """
        return sorted(
            node_ids,
            key=lambda nid: (-self.get_effective_priority(nid), nid)
        )
