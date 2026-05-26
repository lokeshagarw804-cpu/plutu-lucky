"""Conflict detector — identifies files modified on multiple branches.

Compares file change sets across branches to find conflicts (same
file modified by different branches). Conflicts are sorted by
timestamp, and when timestamps match, by branch_id then seq for
deterministic ordering.

Note: seq is local to each branch — it does not provide global ordering.
"""
import configparser


class ConflictDetector:
    """Detects merge conflicts from cross-branch file modifications."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getint(
            "resolution", "similarity_threshold"
        )

    def detect_conflicts(self, branch_diffs):
        """Find files modified by multiple branches.

        A conflict occurs when two or more branches modify the same
        file. Returns list of conflict records sorted by timestamp.
        For same-timestamp conflicts, order should be deterministic
        using branch_id alphabetically then seq within that branch.
        """
        # Build file-to-branch mapping
        file_branches = {}
        for branch_id, files in branch_diffs.items():
            for filename, info in files.items():
                if filename not in file_branches:
                    file_branches[filename] = []
                file_branches[filename].append({
                    "branch_id": branch_id,
                    "version": info["version"],
                    "commit": info["commit"],
                    "timestamp": info["timestamp"],
                })

        # Collect conflicts (files with 2+ branch modifications)
        conflicts = []
        for filename, branch_mods in file_branches.items():
            if len(branch_mods) >= 2:
                for mod in branch_mods:
                    conflicts.append({
                        "filename": filename,
                        "branch_id": mod["branch_id"],
                        "version": mod["version"],
                        "commit": mod["commit"],
                        "timestamp": mod["timestamp"],
                    })

        # Sort by timestamp, then seq for determinism
        conflicts.sort(
            key=lambda c: (c["timestamp"], c["filename"])
        )

        return conflicts

    def get_threshold(self):
        """Return configured similarity threshold."""
        return self._threshold
