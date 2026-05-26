"""Spatial index builder — main entry point.

Orchestrates the full processing flow: load feeds, normalize records,
build spatial index, execute queries, and compute statistics.
"""
import json
import os

from runtime.feed_loader import FeedLoader
from runtime.normalizer import RecordNormalizer
from runtime.indexer import RTreeIndexer
from runtime.query_engine import QueryEngine
from runtime.stats import StatisticsAggregator


def main():
    config_path = "/app/runtime/config.ini"

    loader = FeedLoader(config_path)
    raw_records = loader.load_all_feeds()

    normalizer = RecordNormalizer(config_path)
    records = normalizer.normalize(raw_records)

    indexer = RTreeIndexer(config_path)
    indexer.build_index(records)

    engine = QueryEngine(config_path, indexer)
    query_results = engine.execute_region_query()

    aggregator = StatisticsAggregator(config_path, indexer)
    stats = aggregator.compute_statistics()

    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "query_results.json"), "w") as f:
        json.dump(query_results, f, indent=2)

    with open(os.path.join(output_dir, "index_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    main()
