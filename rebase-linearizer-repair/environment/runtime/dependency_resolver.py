"""Dependency resolver -- groups commits by shared file paths and determines
dependency chains for topological ordering.

Processes commit records to identify which commits modify overlapping files,
forming dependency groups. Commits matching configured skip patterns are
excluded from the dependency graph before grouping occurs.

The skip pattern list is loaded from the [patches] section at initialization
time. Patterns are matched as prefixes against each commit's patch_type field.
"""
import configparser


class DependencyResolver:
    """Resolves commit dependencies based on shared file modifications."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._skip = set(self._config.get("patches", "skip_patterns").split(","))
        self._fallback = self._config.get("patches", "fallback_strategy")

    def resolve(self, commits):
        """Resolve dependencies among commits by shared file paths.

        First filters out commits whose patch_type matches any configured skip
        pattern prefix. Then groups remaining commits that share at least one
        modified file path into dependency groups.

        Returns tuple of (filtered_commits, dependency_groups) where each group
        is a list of commits sharing file modifications.
        """
        filtered = self._filter_skipped(commits)
        groups = self._build_groups(filtered)
        return filtered, groups

    def _filter_skipped(self, commits):
        """Remove commits whose patch_type matches a skip pattern prefix."""
        result = []
        for commit in commits:
            patch_type = commit["patch_type"]
            should_skip = False
            for pattern in self._skip:
                if patch_type.startswith(pattern):
                    should_skip = True
                    break
            if not should_skip:
                result.append(commit)
        return result

    def _build_groups(self, commits):
        """Group commits that share modified file paths.

        Two commits belong to the same group if they share at least one file
        in their files_modified lists. Groups are built using union-find style
        merging -- if commit A shares a file with B, and B shares a file with
        C, then A, B, and C are all in the same group.
        """
        # Map each file to the set of commit indices that modify it
        file_to_commits = {}
        for idx, commit in enumerate(commits):
            for fpath in commit["files_modified"]:
                if fpath not in file_to_commits:
                    file_to_commits[fpath] = set()
                file_to_commits[fpath].add(idx)

        # Union-find to merge overlapping sets
        parent = list(range(len(commits)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for indices in file_to_commits.values():
            indices_list = list(indices)
            for i in range(1, len(indices_list)):
                union(indices_list[0], indices_list[i])

        # Collect groups
        group_map = {}
        for idx in range(len(commits)):
            root = find(idx)
            if root not in group_map:
                group_map[root] = []
            group_map[root].append(commits[idx])

        # Sort groups by earliest timestamp
        groups = sorted(group_map.values(), key=lambda g: g[0]["timestamp"])
        return groups
