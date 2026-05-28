"""Conflict detector -- identifies commit pairs with overlapping file modifications.

Analyzes pairs of commits from different branches to detect potential rebase
conflicts. A conflict occurs when two commits from different branches modify
a number of shared files that meets or exceeds the configured overlap threshold.

The strict detection profile (detection.strict) should be used for production
accuracy as it catches narrower overlaps.
"""
import configparser


class ConflictDetector:
    """Detects rebase conflicts based on file modification overlap."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getint("detection", "overlap_threshold")
        self._max_distance = self._config.getint("detection", "max_file_distance")

    def detect(self, commits):
        """Detect conflicts among commits from different branches.

        Compares every pair of commits from different branches. If the number
        of shared files in their files_modified lists meets or exceeds the
        threshold, the pair is flagged as a conflict.

        Returns list of conflict records, each containing the two commit IDs,
        shared files, and overlap count.
        """
        conflicts = []
        seen_pairs = set()

        for i, commit_a in enumerate(commits):
            for j, commit_b in enumerate(commits):
                if i >= j:
                    continue
                if commit_a["source_branch"] == commit_b["source_branch"]:
                    continue

                pair_key = (commit_a["commit_id"], commit_b["commit_id"])
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                files_a = set(commit_a["files_modified"])
                files_b = set(commit_b["files_modified"])
                shared = files_a & files_b

                if len(shared) >= self._threshold:
                    conflicts.append({
                        "commit_a": commit_a["commit_id"],
                        "commit_b": commit_b["commit_id"],
                        "branch_a": commit_a["source_branch"],
                        "branch_b": commit_b["source_branch"],
                        "shared_files": sorted(shared),
                        "overlap_count": len(shared),
                    })

        conflicts.sort(key=lambda c: (c["commit_a"], c["commit_b"]))
        return conflicts
