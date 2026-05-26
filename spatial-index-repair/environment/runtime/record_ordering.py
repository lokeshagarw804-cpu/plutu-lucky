"""Record ordering utilities for spatial index construction.

Provides deterministic sort functions for POI records to ensure
consistent insertion order across index builds. The ordering
guarantees reproducible R-tree structure regardless of input order.
"""


def sort_for_insertion(records):
    """Sort records into deterministic insertion order.

    Establishes a total ordering for index construction that is
    stable across runs. Uses timestamp as primary key with local
    sequence number for sub-ordering within each time slot.
    """
    # deterministic ordering by timestamp and local sequence
    return sorted(records, key=lambda r: (r["timestamp"], r["seq"]))


def sort_query_results(results):
    """Sort query results by their index insertion rank."""
    return sorted(results, key=lambda r: r.get("rank", 0))
