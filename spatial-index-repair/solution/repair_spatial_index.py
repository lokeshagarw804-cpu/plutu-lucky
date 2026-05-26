#!/usr/bin/env python3
"""Repair script for spatial index builder."""
import os
import sys


def patch_normalizer():
    """Fix category filter whitespace handling in normalizer."""
    path = "/app/runtime/normalizer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._allowed = set(raw_categories.split(","))',
        'self._allowed = set(item.strip() for item in raw_categories.split(","))'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_indexer():
    """Fix config section reference in indexer."""
    path = "/app/runtime/indexer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._batch_size = self._config.getint("spatial.engine", "batch_size")',
        'self._batch_size = self._config.getint("spatial.engine.leafnode", "batch_size")'
    )
    content = content.replace(
        '"spatial.engine", "max_entries_per_node"',
        '"spatial.engine.leafnode", "max_entries_per_node"'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_query_boundary():
    """Fix strict boundary comparison in query_region."""
    path = "/app/runtime/indexer.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'lon_min <= entry["lon"] < lon_max)',
        'lon_min <= entry["lon"] <= lon_max)'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_record_ordering():
    """Fix sort key to include feed_id for cross-stream determinism."""
    path = "/app/runtime/record_ordering.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'key=lambda r: (r["timestamp"], r["seq"])',
        'key=lambda r: (r["timestamp"], r["feed_id"], r["seq"])'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_partition_merger():
    """Fix accumulation to use last-write-wins for partition snapshots."""
    path = "/app/runtime/partition_merger.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._merged[category] = self._merged.get(category, 0) + count',
        'self._merged[category] = count'
    )
    with open(path, "w") as f:
        f.write(content)


def patch_stats():
    """Fix config section reference in statistics aggregator."""
    path = "/app/runtime/stats.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace(
        'self._batch_size = self._config.getint("spatial.engine", "batch_size")',
        'self._batch_size = self._config.getint("spatial.engine.leafnode", "batch_size")'
    )
    content = content.replace(
        '"spatial.engine", "max_entries_per_node"',
        '"spatial.engine.leafnode", "max_entries_per_node"'
    )
    with open(path, "w") as f:
        f.write(content)


def main():
    patch_normalizer()
    patch_indexer()
    patch_query_boundary()
    patch_record_ordering()
    patch_partition_merger()
    patch_stats()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_spatial import main as run_main
    run_main()


if __name__ == "__main__":
    main()
