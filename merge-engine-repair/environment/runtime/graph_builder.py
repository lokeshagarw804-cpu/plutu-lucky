"""Graph builder — assembles the merged commit graph.

Constructs the final merged commit graph from all branches,
incorporating conflict resolutions. Produces the unified history
with proper ancestry tracking and merge metadata.
"""


class GraphBuilder:
    """Builds unified commit graph from merged branches."""

    def __init__(self):
        self._commits = {}

    def build_graph(self, branches, resolutions, depths):
        """Assemble merged commit graph.

        Collects all commits from all branches, attaches depth
        information, and produces the unified graph sorted by
        timestamp ascending.
        """
        all_commits = []

        for branch_id, branch_data in branches.items():
            for commit in branch_data["commits"]:
                all_commits.append({
                    "hash": commit["hash"],
                    "branch_id": branch_id,
                    "timestamp": commit["timestamp"],
                    "parent": commit["parent"],
                    "message": commit["message"],
                    "depth": depths.get(commit["hash"], 0),
                    "files_touched": len(commit["files"]),
                    "seq": commit["seq"],
                })

        # Sort chronologically
        all_commits.sort(key=lambda c: (c["timestamp"], c["seq"]))

        # Summary
        resolved_files = [r["filename"] for r in resolutions]
        branch_ids = sorted(branches.keys())

        # Max depth across all branches
        max_depth = depths.get("__max__", 0)

        return {
            "total_commits": len(all_commits),
            "branches": branch_ids,
            "branch_count": len(branch_ids),
            "commits": all_commits,
            "max_depth": max_depth,
            "conflicts_resolved": len(resolutions),
            "resolved_files": sorted(set(resolved_files)),
        }
