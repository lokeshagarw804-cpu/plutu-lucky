#!/usr/bin/env python3
"""Repair script for spatial query planner."""
import os
import sys


def patch_loader():
    """Fix Bug A: strip whitespace from split source list."""
    path = "/app/runtime/loader.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._active = set(raw_sources.split(","))',
        'self._active = set(s.strip() for s in raw_sources.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_range_query():
    """Fix Bug B: read radius from query.spatial section.
    Fix Bug D: add source_id to sort key for deterministic ordering.
    """
    path = "/app/runtime/range_query.py"
    with open(path, "r") as f:
        content = f.read()
    # Fix Bug B: wrong config section
    content = content.replace(
        'self._radius_km = self._config.getfloat("query", "radius_km")',
        'self._radius_km = self._config.getfloat("query.spatial", "radius_km")'
    )
    content = content.replace(
        'self._max_results = self._config.getint("query", "max_results")',
        'self._max_results = self._config.getint("query.spatial", "max_results")'
    )
    # Fix Bug D: add source_id to sort key
    content = content.replace(
        'results.sort(key=lambda r: (r["distance_km"], r["feature_id"]))',
        'results.sort(key=lambda r: (r["distance_km"], r["source_id"], r["feature_id"]))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_index_builder():
    """Fix Bug C: use accumulation instead of overwrite for feature_count."""
    path = "/app/runtime/index_builder.py"
    with open(path, "r") as f:
        content = f.read()
    # Fix: replace snapshot overwrite with proper accumulation
    content = content.replace(
        '# Note: feature_count tracks features in latest batch for cell\n'
        '                cells[cell_key]["feature_count"] = envelope["feature_count"]',
        '# Note: feature_count tracks total features across all batches\n'
        '                cells[cell_key]["feature_count"] += envelope["feature_count"]'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_loader()
    patch_range_query()
    patch_index_builder()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_query import main as run_main
    run_main()


if __name__ == "__main__":
    main()
