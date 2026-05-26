"""Spatial index builder — main entry point.

Reads POI records from feed files, filters by allowed categories,
builds an R-tree spatial index, executes bounding-box queries, and
writes results and statistics to output directory.
"""
import json
import os
import sys

from runtime.feed_loader import FeedLoader
from runtime.indexer import RTreeIndexer
from runtime.query_engine import QueryEngine
from runtime.stats import StatisticsAggregator


def main():
    config_path = "/app/runtime/config.ini"
    loader = FeedLoader(config_path)
    records = loader.load_all_feeds()

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
