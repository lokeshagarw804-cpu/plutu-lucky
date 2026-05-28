#!/usr/bin/env python3
"""Repair script for rebase linearization engine."""
import sys


def patch_dependency_resolver():
    """Fix skip pattern parsing to handle whitespace in config entries."""
    path = "/projects/sandbox/plutu-lucky/rebase-linearizer-repair/_validate/app/runtime/dependency_resolver.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._skip = set(self._config.get("patches", "skip_patterns").split(","))',
        'self._skip = set(p.strip() for p in self._config.get("patches", "skip_patterns").split(","))'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_conflict_detector():
    """Fix threshold source to use production settings."""
    path = "/projects/sandbox/plutu-lucky/rebase-linearizer-repair/_validate/app/runtime/conflict_detector.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._threshold = self._config.getint("detection", "overlap_threshold")',
        'self._threshold = self._config.getint("detection.strict", "overlap_threshold")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_priority_scorer():
    """Fix group scoring aggregation semantics."""
    path = "/projects/sandbox/plutu-lucky/rebase-linearizer-repair/_validate/app/runtime/priority_scorer.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "priority += patch[\"weight\"]",
        "priority = patch[\"weight\"]"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_dependency_resolver()
    patch_conflict_detector()
    patch_priority_scorer()

    # Re-run with fixed code
    sys.path.insert(0, "/projects/sandbox/plutu-lucky/rebase-linearizer-repair/_validate/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_rebase import main as run_main
    run_main()


if __name__ == "__main__":
    main()
