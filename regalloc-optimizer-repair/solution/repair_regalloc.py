#!/usr/bin/env python3
# PLUTU-LUCKY-CANARY
"""
Register Allocator Repair Script
Patches 5 bugs across the runtime modules and re-runs the pipeline.
"""

import os
import subprocess
import sys


def patch_file(filepath: str, old: str, new: str, description: str) -> bool:
    """Apply a single patch to a file."""
    with open(filepath, "r") as f:
        content = f.read()

    if old not in content:
        print(f"  WARNING: Patch target not found for: {description}")
        print(f"  File: {filepath}")
        return False

    content = content.replace(old, new, 1)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"  FIXED: {description}")
    return True


def find_runtime_dir():
    """Locate the runtime directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    candidate = os.path.join(base_dir, "environment", "runtime")
    if os.path.isdir(candidate):
        return candidate

    candidate = "/app/runtime"
    if os.path.isdir(candidate):
        return candidate

    candidate = os.path.join(base_dir, "runtime")
    if os.path.isdir(candidate):
        return candidate

    raise RuntimeError("Cannot locate runtime directory")


def main():
    """Apply all patches and re-run the pipeline."""
    runtime_dir = find_runtime_dir()
    print("=" * 60)
    print("Register Allocator Repair - Applying Patches")
    print("=" * 60)
    print(f"Runtime directory: {runtime_dir}")
    print()

    patches_applied = 0
    patches_failed = 0

    # Bug 1: liveness_analyzer.py - PHI node liveness over-approximation
    print("[1/5] Liveness Analyzer - PHI operand propagation")
    ok = patch_file(
        os.path.join(runtime_dir, "liveness_analyzer.py"),
        "        for operand_val, from_block in phi.operands:\n"
        "            # add operand to live-out of corresponding predecessor\n"
        "            for pred_id in predecessors:\n"
        "                live_out[pred_id].add(operand_val)",
        "        for operand_val, from_block in phi.operands:\n"
        "            # add operand to live-out of corresponding predecessor\n"
        "            live_out[from_block].add(operand_val)",
        "Only add PHI operand to live-out of its corresponding predecessor"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 2: interference_graph.py - Spill weight formula inversion
    print("[2/5] Interference Graph - Spill weight formula")
    ok = patch_file(
        os.path.join(runtime_dir, "interference_graph.py"),
        "        node.spill_weight = uses * max(node.degree, 1)",
        "        node.spill_weight = uses / max(node.degree, 1)",
        "Use division instead of multiplication for spill weight"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 3: graph_coloring.py - Pre-colored register exclusion
    print("[3/5] Graph Coloring - Pre-colored neighbor exclusion")
    ok = patch_file(
        os.path.join(runtime_dir, "graph_coloring.py"),
        "            if neighbor.color is not None and neighbor_reg in colored_set:\n"
        "                used_colors.add(neighbor.color)",
        "            if neighbor.color is not None:\n"
        "                used_colors.add(neighbor.color)",
        "Check only neighbor.color is not None (not colored_set membership)"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 4: scheduler.py - Anti-dependency operand swap
    print("[4/5] Scheduler - Anti-dependency detection")
    ok = patch_file(
        os.path.join(runtime_dir, "scheduler.py"),
        "            flow_deps = instructions[i].defs & instructions[j].uses\n"
        "            if flow_deps:\n"
        "                edges.append(DepEdge(i, j, HazardType.WAR, 1))",
        "            anti_deps = instructions[i].uses & instructions[j].defs\n"
        "            if anti_deps:\n"
        "                edges.append(DepEdge(i, j, HazardType.WAR, 1))",
        "Check i.uses & j.defs for anti-deps instead of i.defs & j.uses"
    )
    patches_applied += ok
    patches_failed += (not ok)

    # Bug 5: coalescing_engine.py - Briggs criterion off-by-one
    print("[5/5] Coalescing Engine - Briggs criterion threshold")
    ok = patch_file(
        os.path.join(runtime_dir, "coalescing_engine.py"),
        "            if neighbor_degree > K:\n"
        "                significant_count += 1",
        "            if neighbor_degree >= K:\n"
        "                significant_count += 1",
        "Use >= K instead of > K for significant degree check"
    )
    patches_applied += ok
    patches_failed += (not ok)

    print()
    print(f"Patches applied: {patches_applied}/5")
    if patches_failed:
        print(f"Patches FAILED: {patches_failed}/5")
        sys.exit(1)

    # Re-run the pipeline
    print()
    print("Re-running pipeline with fixes applied...")
    print("-" * 60)

    pipeline_cwd = os.path.dirname(runtime_dir)
    result = subprocess.run(
        [sys.executable, "-m", "runtime.pipeline"],
        cwd=pipeline_cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Pipeline FAILED:")
        print(result.stderr)
        sys.exit(1)

    print(result.stdout)
    print("=" * 60)
    print("All patches applied successfully. Pipeline output regenerated.")
    print("=" * 60)


if __name__ == "__main__":
    main()
