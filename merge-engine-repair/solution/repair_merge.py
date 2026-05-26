#!/usr/bin/env python3
"""Repair script for the three-way merge engine."""
import os
import sys


def patch_diff_engine():
    """Fix Bug A: off-by-one in region end boundary (exclusive vs inclusive)."""
    path = "/app/runtime/diff_engine.py"
    with open(path, "r") as f:
        content = f.read()
    # Fix modification region end: should be i-1 not start+(i-start)
    content = content.replace(
        "region_end = region_start + (i - region_start)",
        "region_end = i - 1"
    )
    # Fix addition region end
    content = content.replace(
        "end=base_len + len(added_lines),",
        "end=base_len + len(added_lines) - 1,"
    )
    # Fix deletion region end
    content = content.replace(
        "end=branch_len + len(deleted_lines),",
        "end=branch_len + len(deleted_lines) - 1,"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_conflict_detector():
    """Fix Bug B: wrong boolean logic in conflict condition."""
    path = "/app/runtime/conflict_detector.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "return not has_overlap or either_is_addition",
        "return has_overlap and not either_is_addition"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_resolver():
    """Fix Bug C: shared mutable context causes depth corruption."""
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()
    # The fix: don't accumulate depth across iterations.
    # The bug is that context["depth"] += 1 at the start of _resolve_pair
    # increments the SHARED context dict, and even though it decrements
    # at the end, the resolved_count also grows, and critically: if an
    # early return happens (max_depth_exceeded), the depth is only
    # decremented ONCE but was incremented for each pair.
    # The real fix: pass a copy of context to prevent cross-iteration pollution
    content = content.replace(
        "            resolution = self._resolve_pair(\n                region_a, region_b, context\n            )",
        "            resolution = self._resolve_pair(\n                region_a, region_b, dict(context)\n            )"
    )
    with open(path, "w") as f:
        f.write(content)


def patch_assembler():
    """Fix Bug D: slice uses exclusive end but ranges are inclusive."""
    path = "/app/runtime/assembler.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        "del merged[start:end]",
        "del merged[start:end+1]"
    )
    content = content.replace(
        "merged[start:end] = change[\"lines\"]",
        "merged[start:end+1] = change[\"lines\"]"
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_diff_engine()
    patch_conflict_detector()
    patch_resolver()
    patch_assembler()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_merge import main as run_main
    run_main()


if __name__ == "__main__":
    main()
