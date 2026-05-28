"""Linearizer -- produces a topologically-ordered commit sequence.

Takes scored dependency groups and produces a flat, deterministic commit
sequence suitable for rebase application. Uses priority scores to order
groups and timestamps to break ties within groups.
"""
import configparser


class Linearizer:
    """Produces a linearized commit sequence from scored dependency groups."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._method = self._config.get("ordering", "method")
        self._tie_break = self._config.get("ordering", "break_ties_by")
        self._deterministic = self._config.getboolean("ordering", "deterministic")

    def linearize(self, scored_groups, filtered_commits):
        """Produce a linearized commit sequence.

        Orders groups by priority (descending), then arranges commits
        within each group by timestamp for deterministic output.

        Returns ordered list of commit records representing the rebase plan.
        """
        # Sort groups by priority descending, then by earliest timestamp
        ordered_groups = sorted(
            scored_groups,
            key=lambda g: (-g["priority"], g["earliest_timestamp"])
        )

        # Build commit lookup
        commit_map = {c["commit_id"]: c for c in filtered_commits}

        # Flatten into ordered commit sequence
        linearized = []
        seen = set()
        for group in ordered_groups:
            # Within a group, order commits by timestamp
            group_commits = []
            for cid in group["commits"]:
                if cid in commit_map and cid not in seen:
                    group_commits.append(commit_map[cid])
                    seen.add(cid)

            group_commits.sort(key=lambda c: c["timestamp"])
            linearized.extend(group_commits)

        return linearized
