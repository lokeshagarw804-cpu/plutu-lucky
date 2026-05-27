"""Spatial query planner — main entry point.

Orchestrates the spatial query process: load source data, build
spatial index, execute range query, and produce output reports.
"""
import json
import os

from runtime.loader import SourceLoader
from runtime.index_builder import IndexBuilder
from runtime.range_query import RangeQueryExecutor
from runtime.report_builder import ReportBuilder


def main():
    config_path = "/app/runtime/config.ini"

    # Load feature data from configured sources
    loader = SourceLoader(config_path)
    sources = loader.load_sources()

    # Flatten all features with source attribution
    all_features = []
    for source_id, features in sources.items():
        for f in features:
            f["source_id"] = source_id
            all_features.append(f)

    # Build spatial index
    builder = IndexBuilder(config_path)
    index = builder.build_index(all_features)

    # Execute range query
    executor = RangeQueryExecutor(config_path)
    results = executor.execute(all_features)

    # Compute index statistics
    index_stats = {
        "total_cells": len(index),
        "total_features": sum(c["feature_count"] for c in index.values()),
    }

    # Build reports
    reporter = ReportBuilder()
    summary, detailed_results = reporter.build_report(
        results, index_stats, list(sources.keys())
    )

    # Write output
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "query_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(output_dir, "query_results.json"), "w") as f:
        json.dump({"results": detailed_results}, f, indent=2)

    with open(os.path.join(output_dir, "index_stats.json"), "w") as f:
        json.dump({
            "cells": {k: v for k, v in index.items()},
            "total_cells": len(index),
            "total_features": index_stats["total_features"],
        }, f, indent=2)


if __name__ == "__main__":
    main()
