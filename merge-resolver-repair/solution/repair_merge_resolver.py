#!/usr/bin/env python3
"""Repair script for merge resolution engine."""
import os
import sys


def patch_differ():
    """Fix strategy list parsing to strip whitespace from config entries."""
    path = "/app/runtime/differ.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug A: strip whitespace from strategy names after split
    content = content.replace(
        'self._strategies = set(raw_strategies.split(","))',
        'self._strategies = set(item.strip() for item in raw_strategies.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_classifier():
    """Fix threshold to read from merge.strict config section."""
    path = "/app/runtime/classifier.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug B: read from merge.strict section instead of merge
    content = content.replace(
        'self._threshold = self._config.getint("merge", "conflict_threshold")',
        'self._threshold = self._config.getint("merge.strict", "conflict_threshold")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_scorer():
    """Fix region scoring to use last-write-wins instead of accumulation."""
    path = "/app/runtime/scorer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: replace accumulation with last-write-wins
    old_scoring = """        score = 0
        for hunk in region_hunks:
            severity = 100 - hunk["similarity_score"]
            score += severity
        return score"""

    new_scoring = """        score = 0
        for hunk in region_hunks:
            severity = 100 - hunk["similarity_score"]
            score = severity
        return score"""

    content = content.replace(old_scoring, new_scoring)

    with open(path, "w") as f:
        f.write(content)


def patch_resolver():
    """Fix conflict ordering to include branch_id in sort key."""
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug D: add branch_id to sort key for deterministic ordering
    content = content.replace(
        'conflicts.sort(key=lambda c: (c["line_start"], c["hunk_id"]))',
        'conflicts.sort(key=lambda c: (c["line_start"], c["branch_id"], c["hunk_id"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_differ()
    patch_classifier()
    patch_scorer()
    patch_resolver()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_merge import main as run_main
    run_main()


if __name__ == "__main__":
    main()
