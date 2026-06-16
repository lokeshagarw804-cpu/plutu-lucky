#!/usr/bin/env python3
"""Repair script for multi-tier cache system.

Patches defects in runtime source files and re-runs the system.
"""
import sys


def patch_eviction():
    """Fix cache access method and eviction victim selection.

    Bug 1: The access method speculatively writes an L1 timestamp
    before verifying the key exists in L1. This wastes a sequence
    number on every non-L1 access, skewing the timestamp space.
    Fix: check L1 membership first, then update timestamp on hit.

    Bug 4: The victim selection sorts timestamps ascending.
    Since timestamps are stored as (base - seq), smaller values
    are more recent. Ascending sort picks the most-recent entry
    as victim — the opposite of LRU. Fix: sort descending.
    """
    path = "/app/runtime/eviction.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug 1: Move timestamp update after existence check
    old_access = (
        '        # Record access for freshness tracking\n'
        '        self._l1_timestamps[key] = self._next_timestamp()\n'
        '        if key in self._l1_store:\n'
        '            return self._l1_store[key], "l1"\n'
        '\n'
        '        # Not in L1 \u2014 clean up speculative timestamp\n'
        '        del self._l1_timestamps[key]'
    )
    new_access = (
        '        if key in self._l1_store:\n'
        '            self._l1_timestamps[key] = self._next_timestamp()\n'
        '            return self._l1_store[key], "l1"'
    )
    content = content.replace(old_access, new_access)

    # Fix Bug 4: Reverse sort to evict largest timestamp (oldest access)
    old_sort = (
        '        candidates.sort(key=lambda k: store_timestamps[k])\n'
        '        return candidates[0]'
    )
    new_sort = (
        '        candidates.sort(key=lambda k: store_timestamps[k], reverse=True)\n'
        '        return candidates[0]'
    )
    content = content.replace(old_sort, new_sort)

    with open(path, "w") as f:
        f.write(content)


def patch_promoter():
    """Fix promotion threshold config section.

    The promoter reads from [promotion] (threshold=5) instead of
    [promotion.tuned] (threshold=3). This makes promotion harder
    than intended — entries need 5 hits rather than 3.
    """
    path = "/app/runtime/promoter.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        'self._threshold = config.getint("promotion", "threshold")',
        'self._threshold = config.getint("promotion.tuned", "threshold")'
    )

    with open(path, "w") as f:
        f.write(content)


def patch_reporter():
    """Fix hit rate accumulator in reporter.

    The loop overwrites total_hits with each client's hits instead
    of accumulating. Only the last client's hits end up in the
    total, producing an incorrect overall hit rate.
    """
    path = "/app/runtime/reporter.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "total_hits = client_hits",
        "total_hits += client_hits"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_eviction()
    patch_promoter()
    patch_reporter()

    import subprocess
    result = subprocess.run(
        ["python3", "-m", "runtime.main"],
        cwd="/app",
        capture_output=True
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
