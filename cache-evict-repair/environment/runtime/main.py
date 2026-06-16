"""Main entry point for multi-tier cache system.

Orchestrates the cache processing pipeline:
1. Load client access streams
2. Process requests through tiered cache
3. Handle tier promotions
4. Generate performance reports
"""
from runtime.loader import load_all_streams, get_config
from runtime.eviction import TieredCache
from runtime.promoter import PromotionManager
from runtime.reporter import PerformanceReporter


def process_streams(config, streams, cache, promoter):
    """Process all client streams through the cache system.

    Each client's requests are processed sequentially. After each
    L2 hit, the promotion manager evaluates whether the entry
    should be elevated to L1.

    Args:
        config: Application configuration.
        streams: Dict mapping client names to request lists.
        cache: TieredCache instance.
        promoter: PromotionManager instance.

    Returns:
        List of per-client statistics dicts.
    """
    all_stats = []

    for client_name in sorted(streams.keys()):
        requests = streams[client_name]
        client_stats = {
            "client": client_name,
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "promotions": 0,
        }

        for req in requests:
            key = req["key"]
            value, tier = cache.access(key)

            if tier == "l1":
                client_stats["l1_hits"] += 1
            elif tier == "l2":
                client_stats["l2_hits"] += 1
                promoter.attempt_promotion(cache, key, client_stats)
            else:
                client_stats["misses"] += 1

        all_stats.append(client_stats)

    return all_stats


def main():
    """Run the complete cache processing pipeline."""
    config = get_config()
    streams = load_all_streams(config)
    cache = TieredCache(config)
    promoter = PromotionManager(config)

    client_stats = process_streams(config, streams, cache, promoter)

    output_dir = config.get("cache", "output_dir")
    reporter = PerformanceReporter(output_dir)
    summary = reporter.write_reports(client_stats, cache.eviction_count)

    return summary


if __name__ == "__main__":
    main()
