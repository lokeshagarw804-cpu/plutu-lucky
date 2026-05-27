"""Metric aggregation engine — main entry point.

Orchestrates the full performance analysis pipeline: load service node
metrics, filter and align time ranges, aggregate into windows, compute
degradation rankings, detect incidents, and generate health report.
"""
import json
import os

from runtime.loader import MetricLoader
from runtime.filter import MetricFilter
from runtime.aggregator import MetricAggregator
from runtime.ranker import MetricRanker
from runtime.detector import IncidentDetector
from runtime.reporter import HealthReporter


def main():
    config_path = "/app/runtime/config.ini"

    # Stage 1: Load metric data
    loader = MetricLoader(config_path)
    raw_nodes = loader.load_nodes()

    # Stage 2: Filter and align time ranges
    metric_filter = MetricFilter()
    filtered = metric_filter.filter_aligned(raw_nodes)

    # Stage 3: Aggregate into windows
    aggregator = MetricAggregator(config_path)
    aggregated = aggregator.aggregate(filtered)

    # Stage 4: Rank nodes by degradation
    ranker = MetricRanker(config_path)
    ranked = ranker.rank_nodes(aggregated)

    # Stage 5: Detect degradation incidents
    detector = IncidentDetector(config_path)
    incidents = detector.detect_incidents(ranked)

    # Stage 6: Generate health report
    reporter = HealthReporter()
    report = reporter.generate_report(ranked, incidents)

    # Write output
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "health_report.json"), "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
