#!/usr/bin/env python3
"""Repair script for spatial index builder.

Patches four defects in the runtime source files and re-runs the system
to produce correct output.
"""
import os
import sys


def patch_feed_loader():
    """Fix Bug A: category filter whitespace handling.
    
    The config value 'restaurant,park,museum, hospital' has a space before
    'hospital'. The split(',') produces ' hospital' which never matches.
    Fix: strip each item after splitting.
    """
    path = "/app/runtime/feed_loader.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._allowed = set(raw_categories.split(","))',
        'self._allowed = set(item.strip() for item in raw_categories.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_indexer_config():
    """Fix Bug B: wrong config section for R-tree parameters.
    
    The indexer reads batch_size and max_entries_per_node from [indexer] section
    (values 100 and 50) instead of [indexer.rtree] section (values 20 and 8).
    """
    path = "/app/runtime/indexer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._batch_size = self._config.getint("indexer", "batch_size")',
        'self._batch_size = self._config.getint("indexer.rtree", "batch_size")'
    )
    content = content.replace(
        'self._max_entries = self._config.getint("indexer", "max_entries_per_node")',
        'self._max_entries = self._config.getint("indexer.rtree", "max_entries_per_node")'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_indexer_sort():
    """Fix Bug D: sort tiebreaker missing feed_id.
    
    Records with identical timestamps are sorted by (timestamp, seq) but seq
    is local to each feed stream. Must include feed_id for deterministic ordering.
    """
    path = "/app/runtime/indexer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda r: (r["timestamp"], r["seq"])',
        'key=lambda r: (r["timestamp"], r["feed_id"], r["seq"])'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_stats_accumulation():
    """Fix Bug C: partition snapshot accumulation.
    
    Stats aggregator sums counts across partitions instead of using the last
    partition's values. Each partition is a snapshot; final stats should reflect
    only the last partition's category distribution.
    """
    path = "/app/runtime/stats.py"
    with open(path, "r") as f:
        content = f.read()
    # Replace the accumulation with last-write-wins
    content = content.replace(
        'category_counts[cat] = category_counts.get(cat, 0) + count',
        'category_counts[cat] = count'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_stats_config():
    """Fix Bug B in stats: wrong config section for batch_size.
    
    The stats aggregator also reads batch_size from [indexer] instead of
    [indexer.rtree], causing incorrect partition boundaries.
    """
    path = "/app/runtime/stats.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._batch_size = self._config.getint("indexer", "batch_size")',
        'self._batch_size = self._config.getint("indexer.rtree", "batch_size")'
    )
    # Also fix the max_entries_per_node read in compute_statistics
    content = content.replace(
        '"max_entries_per_node": self._config.getint("indexer", "max_entries_per_node")',
        '"max_entries_per_node": self._config.getint("indexer.rtree", "max_entries_per_node")'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_feed_loader()
    patch_indexer_config()
    patch_indexer_sort()
    patch_stats_accumulation()
    patch_stats_config()

    # Re-run with fixed code
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_spatial import main as run_main
    run_main()


if __name__ == "__main__":
    main()
