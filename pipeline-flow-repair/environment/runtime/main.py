"""Pipeline flow monitoring — main entry point.

Orchestrates the full pipeline analysis: load segment data, compute
pressure drops, aggregate flow, detect anomalies, classify issues,
and generate the health report.
"""
import json
import os

from runtime.loader import SegmentLoader
from runtime.pressure_calc import PressureCalculator
from runtime.flow_aggregator import FlowAggregator
from runtime.anomaly_detector import AnomalyDetector
from runtime.segment_sorter import SegmentSorter
from runtime.leak_classifier import LeakClassifier
from runtime.report_builder import ReportBuilder


def main():
    config_path = "/app/runtime/config.ini"

    # Load segment data
    loader = SegmentLoader(config_path)
    segments = loader.load_segments()

    # Compute pressure drops
    pressure_calc = PressureCalculator(config_path)
    expected_drops = pressure_calc.compute_expected_drops(segments)
    actual_drops = pressure_calc.compute_actual_drops(segments)

    # Aggregate flow statistics
    aggregator = FlowAggregator(config_path)
    flow_stats = aggregator.aggregate(segments)

    # Order segments by network topology
    sorter = SegmentSorter(config_path)
    segment_order = sorter.sort_segments(segments)

    # Detect anomalies
    detector = AnomalyDetector(config_path)
    pressure_anomalies = detector.detect_pressure_anomalies(
        expected_drops, actual_drops
    )
    flow_anomalies = detector.detect_flow_anomalies(segments, flow_stats)

    # Classify anomalies
    classifier = LeakClassifier(config_path)
    classifications = classifier.classify(pressure_anomalies, segments)

    # Build and write reports
    builder = ReportBuilder()
    report = builder.build_report(
        segments, flow_stats, pressure_anomalies,
        flow_anomalies, classifications, segment_order
    )

    output_dir = "/app/runtime/output"
    builder.write_report(report, output_dir)
    builder.write_flow_summary(flow_stats, segment_order, output_dir)


if __name__ == "__main__":
    main()
