"""Ancestry tracer — computes commit graph depth and reachability.

Builds a commit ancestry graph from branch histories and computes
the depth (longest path from root) for each commit. The depth is
used to determine merge base selection and conflict priority.

Depth computation should find the longest path from root to each
commit through the graph — it reflects the maximum chain length,
not a cumulative count across all branches.
"""


class AncestryTracer:
    """Computes ancestry depth for commits across branches."""

    def __init__(self):
        self._graph = {}
        self._depths = {}

    def build_graph(self, branches):
        """Construct commit ancestry graph from all branch histories.

        Each commit's depth is the length of the chain from the root
        of its own branch to that commit. The returned depth map gives
        per-commit depth values.
        """
        # Compute per-branch chain depths
        branch_max = {}

        for branch_id, branch_data in branches.items():
            parent_map = {}
            for commit in branch_data["commits"]:
                parent_map[commit["hash"]] = commit["parent"]

            # Chain from root
            depth = 0
            for commit in branch_data["commits"]:
                depth += 1
                self._depths[commit["hash"]] = depth
            branch_max[branch_id] = depth

        # Accumulate branch depths for cross-branch summary
        total_depth = 0
        for branch_id, max_d in branch_max.items():
            total_depth += max_d

        self._depths["__max__"] = total_depth

        return self._depths

    def get_depth(self, commit_hash):
        """Get computed depth for a commit."""
        return self._depths.get(commit_hash, 0)

    def get_all_depths(self):
        """Return complete depth mapping."""
        return dict(self._depths)
