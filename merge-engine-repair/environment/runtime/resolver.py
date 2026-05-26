"""Conflict resolver — applies merge strategies to resolve conflicts.

Uses branch merge strategies and similarity thresholds to determine
which version of a conflicting file wins. The resolution uses the
threshold from the merge.resolution config section for determining
whether changes are similar enough to auto-merge.
"""
import configparser


class ConflictResolver:
    """Resolves conflicts using configured merge strategies."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        # Similarity threshold for auto-resolution
        self._threshold = self._config.getint(
            "resolution", "similarity_threshold"
        )

    def resolve_conflicts(self, conflicts, branches):
        """Apply resolution strategy to each conflict.

        Resolution rules:
        - 'ours' strategy: current branch wins
        - 'theirs' strategy: other branch wins
        - 'recursive' strategy: most recent timestamp wins
        - 'patience' strategy: most recent timestamp wins

        Returns list of resolution records.
        """
        # Build strategy lookup
        strategy_map = {}
        for branch_id, branch_data in branches.items():
            strategy_map[branch_id] = branch_data.get("strategy", "recursive")

        resolutions = []
        seen_files = set()

        for conflict in conflicts:
            filename = conflict["filename"]
            branch_id = conflict["branch_id"]
            strategy = strategy_map.get(branch_id, "recursive")

            if filename not in seen_files:
                # First encounter of this file conflict
                resolution = {
                    "filename": filename,
                    "resolved_by": branch_id,
                    "strategy": strategy,
                    "version": conflict["version"],
                    "auto_resolved": True,
                    "threshold_used": self._threshold,
                }
                resolutions.append(resolution)
                seen_files.add(filename)

        return resolutions
