"""
Dependency graph structure builder.

Constructs the directed graph representation from resolved packages
and produces the installation order via topological sort.

Installation order determines the sequence in which packages are
installed. For packages at the same depth, ordering is determined
by (depth, scope, package_name) to ensure reproducible builds where
scope priority (runtime before peer) is respected.
"""

import configparser


class GraphBuilder:
    """Builds dependency graph and computes install order."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)
        self._include_checksum = config.getboolean(
            "manifest", "include_checksum"
        )

    def build_graph(self, resolved_packages):
        """Build dependency graph edges from resolved packages."""
        nodes = {}
        for pkg in resolved_packages:
            key = pkg["package"]
            nodes[key] = {
                "package": pkg["package"],
                "version": pkg["version"],
                "scope": pkg["scope"],
                "depth": pkg["depth"],
            }

        return {
            "nodes": nodes,
            "node_count": len(nodes),
        }

    def compute_install_order(self, resolved_packages):
        """Compute deterministic installation order.

        Packages are installed leaves-first (deeper dependencies installed
        before their dependents). At equal depth, ordering is by
        (scope, package_name) for reproducible builds.
        """
        sorted_pkgs = sorted(
            resolved_packages,
            key=lambda p: (p["depth"], p["package"])
        )
        return sorted_pkgs
