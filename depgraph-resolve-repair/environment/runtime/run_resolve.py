"""
Main entry point for the dependency graph resolution system.

Orchestrates the full resolution process:
1. Load package registry from data files
2. Filter packages by scope exclusion rules
3. Resolve dependencies recursively from root packages
4. Build dependency graph and compute install order
5. Write resolution manifest and outputs
"""

from runtime.loader import load_registry
from runtime.scope_filter import ScopeFilter
from runtime.resolver import DependencyResolver
from runtime.graph_builder import GraphBuilder
from runtime.manifest_writer import ManifestWriter


def main():
    """Run the dependency resolution process."""
    # Stage 1: Load registry
    packages = load_registry()

    # Stage 2: Filter by scope
    scope_filter = ScopeFilter()
    filtered = scope_filter.filter_packages(packages)

    # Stage 3: Resolve dependencies
    resolver = DependencyResolver()
    resolved = resolver.resolve(filtered)

    # Stage 4: Build graph and install order
    builder = GraphBuilder()
    graph = builder.build_graph(resolved)
    install_order = builder.compute_install_order(resolved)

    # Stage 5: Write outputs
    writer = ManifestWriter()
    manifest, graph_out, summary = writer.write_outputs(
        resolved, install_order, graph
    )

    print(f"Resolved {manifest['total_packages']} packages")
    print(f"Max depth: {summary['max_depth_reached']}")
    print(f"Checksum: {manifest['integrity_checksum']}")
    print(f"Scopes: {summary['by_scope']}")


if __name__ == "__main__":
    main()
