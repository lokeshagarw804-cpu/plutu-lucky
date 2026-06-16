"""Tier promotion manager for L2 to L1 cache promotion.

Monitors L2 hit counts and triggers promotion to L1 when entries
exceed the configured access threshold. Uses tunable parameters
from the configuration system to adapt promotion aggressiveness.
"""
import configparser


class PromotionManager:
    """Manages promotion decisions for cache entries.

    Reads promotion parameters from the system configuration and
    evaluates whether L2 entries qualify for L1 tier elevation.
    The promotion section supports multiple tuning profiles;
    the active profile is selected at initialization.
    """

    def __init__(self, config):
        self._config = config
        self._threshold = config.getint("promotion", "threshold")
        self._min_l2_hits = config.getint("promotion", "min_l2_hits")

    @property
    def threshold(self):
        """Current promotion threshold value."""
        return self._threshold

    def should_promote(self, cache, key):
        """Determine if an L2 entry qualifies for promotion.

        An entry is promoted when its L2 hit count reaches the
        configured threshold. The min_l2_hits guard prevents
        promoting entries that have only received burst traffic.

        Args:
            cache: TieredCache instance to query.
            key: Cache key to evaluate.

        Returns:
            True if the entry should be promoted to L1.
        """
        if not cache.is_in_l2(key):
            return False
        hits = cache.get_l2_hits(key)
        if hits < self._min_l2_hits:
            return False
        return hits >= self._threshold

    def attempt_promotion(self, cache, key, client_stats):
        """Try to promote a key and update statistics.

        Args:
            cache: TieredCache instance.
            key: Key to potentially promote.
            client_stats: Dict to update with promotion count.

        Returns:
            True if promotion occurred.
        """
        if self.should_promote(cache, key):
            cache.promote(key)
            client_stats["promotions"] += 1
            return True
        return False
