#!/usr/bin/env python3
"""Repair script for merge engine. Patches all defects and re-runs."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from comma-split strategy list."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._active_strategies = set(raw_strategies.split(","))',
        'self._active_strategies = set(s.strip() for s in raw_strategies.split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_resolver():
    """Fix Bug B: read similarity_threshold from merge.resolution section."""
    path = "/app/runtime/resolver.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._threshold = self._config.getint(\n            "resolution", "similarity_threshold"\n        )',
        'self._threshold = self._config.getint(\n            "merge.resolution", "similarity_threshold"\n        )'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_ancestry():
    """Fix Bug C: use max branch depth instead of sum."""
    path = "/app/runtime/ancestry.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix: replace sum with max for cross-branch depth
    content = content.replace(
        "        # Accumulate branch depths for cross-branch summary\n"
        "        total_depth = 0\n"
        "        for branch_id, max_d in branch_max.items():\n"
        "            total_depth += max_d\n"
        "\n"
        '        self._depths["__max__"] = total_depth',
        "        # Use maximum branch depth for cross-branch summary\n"
        '        self._depths["__max__"] = max(branch_max.values()) if branch_max else 0'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_graph_builder():
    """Fix Bug D: add branch_id as tiebreaker in commit sort."""
    path = "/app/runtime/graph_builder.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'all_commits.sort(key=lambda c: (c["timestamp"], c["seq"]))',
        'all_commits.sort(key=lambda c: (c["timestamp"], c["branch_id"], c["seq"]))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_differ():
    """Fix Bug E: remove off-by-one in chunk boundary calculation."""
    path = "/app/runtime/differ.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "        for i in range(0, len(files), self._chunk_size + 1):\n"
        "            chunk = files[i:i + self._chunk_size + 1]",
        "        for i in range(0, len(files), self._chunk_size):\n"
        "            chunk = files[i:i + self._chunk_size]"
    )

    content = content.replace(
        "        return math.ceil(file_count / (self._chunk_size + 1))",
        "        return math.ceil(file_count / self._chunk_size)"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_resolver()
    patch_ancestry()
    patch_graph_builder()
    patch_differ()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_merge import main as run_main
    run_main()


if __name__ == "__main__":
    main()
