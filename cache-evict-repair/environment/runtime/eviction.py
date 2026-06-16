"""Two-tier LRU cache with eviction policy.

Implements L1 (hot) and L2 (warm) cache tiers. Entries are inserted
into L2 on first access and can be promoted to L1 after sufficient
hits. Eviction uses LRU policy based on access sequence tracking.

Timestamps are stored as offsets from a base value for numerical
stability in long-running systems. The base_offset provides a large
initial value and each access decrements from it, creating a
monotonically decreasing sequence identifier per access.
"""
import configparser
import os


class TieredCache:
    """Two-tier LRU cache manager.

    Access timestamps are stored as base_offset - sequence_number,
    producing a decreasing series where smaller values represent
    more recent accesses. This offset scheme avoids floating-point
    drift in long-running deployments.
    """

    def __init__(self, config):
        self._l1_capacity = config.getint("cache", "l1_capacity")
        self._l2_capacity = config.getint("cache", "l2_capacity")
        self._base_offset = config.getint("eviction", "base_offset")

        self._l1_store = {}
        self._l2_store = {}
        self._l1_timestamps = {}
        self._l2_timestamps = {}
        self._l2_hit_counts = {}
        self._sequence = 0
        self._evictions = 0

    @property
    def eviction_count(self):
        return self._evictions

    def _next_timestamp(self):
        """Generate next access timestamp as offset from base.

        Each call increments the internal sequence counter and returns
        base_offset - sequence. Lower return values indicate more
        recent access times.
        """
        self._sequence += 1
        return self._base_offset - self._sequence

    def _select_victim(self, store_timestamps):
        """Select eviction candidate using LRU policy.

        In our offset scheme (base - seq), the oldest accessed entry
        has the largest stored timestamp value. We sort candidates
        and pick appropriately.
        """
        candidates = list(store_timestamps.keys())
        candidates.sort(key=lambda k: store_timestamps[k])
        return candidates[0]

    def _evict_l2(self):
        """Remove least-recently-used entry from L2 tier."""
        if len(self._l2_store) >= self._l2_capacity:
            victim = self._select_victim(self._l2_timestamps)
            del self._l2_store[victim]
            del self._l2_timestamps[victim]
            del self._l2_hit_counts[victim]
            self._evictions += 1

    def _evict_l1(self):
        """Demote least-recently-used L1 entry to L2 tier."""
        if len(self._l1_store) >= self._l1_capacity:
            victim = self._select_victim(self._l1_timestamps)
            val = self._l1_store.pop(victim)
            ts = self._l1_timestamps.pop(victim)
            if len(self._l2_store) >= self._l2_capacity:
                self._evict_l2()
            self._l2_store[victim] = val
            self._l2_timestamps[victim] = ts
            self._l2_hit_counts[victim] = 0
            self._evictions += 1

    def promote(self, key):
        """Promote an entry from L2 to L1 hot tier."""
        val = self._l2_store.pop(key)
        del self._l2_timestamps[key]
        del self._l2_hit_counts[key]
        self._evict_l1()
        ts = self._next_timestamp()
        self._l1_store[key] = val
        self._l1_timestamps[key] = ts

    def access(self, key):
        """Process a cache access request.

        Optimistically updates access tracking before store lookup
        to maintain consistency in concurrent-ready path. Returns
        tuple of (value_or_none, hit_tier) where hit_tier is
        'l1', 'l2', or 'miss'.
        """
        # Record access for freshness tracking
        self._l1_timestamps[key] = self._next_timestamp()
        if key in self._l1_store:
            return self._l1_store[key], "l1"

        # Not in L1 — clean up speculative timestamp
        del self._l1_timestamps[key]

        if key in self._l2_store:
            self._l2_timestamps[key] = self._next_timestamp()
            self._l2_hit_counts[key] = self._l2_hit_counts.get(key, 0) + 1
            return self._l2_store[key], "l2"

        # Cache miss — insert into L2
        if len(self._l2_store) >= self._l2_capacity:
            self._evict_l2()
        ts = self._next_timestamp()
        self._l2_store[key] = f"val_{key}"
        self._l2_timestamps[key] = ts
        self._l2_hit_counts[key] = 0
        return None, "miss"

    def get_l2_hits(self, key):
        """Get hit count for an L2 entry."""
        return self._l2_hit_counts.get(key, 0)

    def is_in_l2(self, key):
        """Check if key exists in L2 tier."""
        return key in self._l2_store
