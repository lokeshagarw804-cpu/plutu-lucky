"""Merge engine — main entry point.

Orchestrates the full merge analysis: load branch histories, compute
ancestry depths, generate file diffs, detect conflicts, resolve them,
and build the unified commit graph.
"""
import json
import os

from runtime.loader import BranchLoader
from runtime.ancestry import AncestryTracer
from runtime.differ import DiffEngine
from runtime.conflict_detector import ConflictDetector
from runtime.resolver import ConflictResolver
from runtime.graph_builder import GraphBuilder


def main():
    config_path = "/app/runtime/config.ini"

    # Load branch histories
    loader = BranchLoader(config_path)
    branches = loader.load_branches()

    # Compute ancestry depths
    tracer = AncestryTracer()
    depths = tracer.build_graph(branches)

    # Compute file diffs
    differ = DiffEngine(config_path)
    branch_diffs = differ.compute_diffs(branches)

    # Detect conflicts
    detector = ConflictDetector(config_path)
    conflicts = detector.detect_conflicts(branch_diffs)

    # Resolve conflicts
    resolver = ConflictResolver(config_path)
    resolutions = resolver.resolve_conflicts(conflicts, branches)

    # Build merged graph
    builder = GraphBuilder()
    graph = builder.build_graph(branches, resolutions, depths)

    # Compute chunk info for diff analysis
    all_files = set()
    for branch_id, files in branch_diffs.items():
        all_files.update(files.keys())
    chunks = differ.chunk_files(all_files)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    # Merge graph output
    with open(os.path.join(output_dir, "merge_graph.json"), "w") as f:
        json.dump(graph, f, indent=2)

    # Conflict report
    conflict_report = {
        "total_conflicts": len(conflicts),
        "resolutions": resolutions,
        "resolution_count": len(resolutions),
        "similarity_threshold": resolver._threshold,
        "chunk_count": len(chunks),
        "total_files_analyzed": len(all_files),
        "chunks": [{"chunk_id": i, "files": c} for i, c in enumerate(chunks)],
    }
    with open(os.path.join(output_dir, "conflict_report.json"), "w") as f:
        json.dump(conflict_report, f, indent=2)


if __name__ == "__main__":
    main()
