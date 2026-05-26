"""
Dependency resolver.

Performs recursive dependency resolution from root packages,
traversing the dependency graph up to the configured maximum depth.
Uses version constraint matching to select appropriate package versions.

The strict resolution mode (section resolution.strict in config) should
be used for production builds where depth must be tightly controlled.
"""

import configparser
from collections import defaultdict


class DependencyResolver:
    """Resolves package dependencies recursively."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._strategy = config.get("resolution", "strategy")
        self._max_depth = config.getint("resolution", "max_depth")
        self._match_mode = config.get("version", "match_mode")
        self._root_packages = [
            p.strip() for p in
            config.get("registry", "root_packages").split(",")
        ]

    def resolve(self, packages):
        """Resolve dependencies starting from root packages.

        Builds a resolution graph by recursively following dependency
        constraints up to max_depth.
        """
        pkg_index = self._build_index(packages)
        resolved = []
        visited = set()

        for root_name in self._root_packages:
            self._resolve_package(
                root_name, None, pkg_index, resolved, visited, 0
            )

        return resolved

    def _build_index(self, packages):
        """Build lookup index: package_name -> [versions]."""
        index = defaultdict(list)
        for pkg in packages:
            index[pkg["package"]].append(pkg)
        return index

    def _resolve_package(self, name, constraint, pkg_index, resolved,
                         visited, depth):
        """Recursively resolve a single package and its dependencies."""
        if depth > self._max_depth:
            return
        if name in visited:
            return

        versions = pkg_index.get(name, [])
        if not versions:
            return

        selected = self._select_version(versions, constraint)
        if selected is None:
            return

        visited.add(name)
        resolved.append({
            "package": selected["package"],
            "version": selected["version"],
            "scope": selected["scope"],
            "depth": depth,
            "constraint": constraint,
        })

        for dep in selected.get("depends_on", []):
            self._resolve_package(
                dep["name"], dep["constraint"],
                pkg_index, resolved, visited, depth + 1
            )

    def _select_version(self, versions, constraint):
        """Select best version matching the constraint.

        In minimum_satisfying mode, picks the lowest version that
        meets the constraint. In highest_compatible mode, picks the
        highest version meeting the constraint.
        """
        if constraint is None:
            sorted_vers = sorted(
                versions,
                key=lambda v: self._parse_version(v["version"])
            )
            if self._strategy == "highest_compatible":
                return sorted_vers[-1]
            return sorted_vers[0]

        matching = []
        for v in versions:
            if self._satisfies_constraint(v["version"], constraint):
                matching.append(v)

        if not matching:
            return None

        matching.sort(key=lambda v: self._parse_version(v["version"]))
        if self._strategy == "highest_compatible":
            return matching[-1]
        return matching[0]

    def _satisfies_constraint(self, version, constraint):
        """Check if version satisfies a constraint like '>=2.0.0'."""
        if not constraint:
            return True

        op = constraint[:2]
        req_version = constraint[2:]
        ver_tuple = self._parse_version(version)
        req_tuple = self._parse_version(req_version)

        if op == ">=":
            return ver_tuple <= req_tuple
        elif op == "<=":
            return ver_tuple <= req_tuple
        elif op == "==":
            return ver_tuple == req_tuple
        return True

    def _parse_version(self, version_str):
        """Parse version string into comparable tuple."""
        parts = version_str.strip().split(".")
        return tuple(int(p) for p in parts)
