#!/usr/bin/env python3
"""
Sensor Fusion Calibration Pipeline Runner

Orchestrates the full calibration pipeline:
1. Load cluster data
2. Normalize readings
3. Apply drift compensation
4. Compute cross-sensor correlations
5. Score sensor confidence
6. Assemble calibration matrix
7. Generate final report

Usage:
    python run_calibration.py [--data-dir PATH] [--config PATH] [--output PATH]
"""

import json
import os
import sys
from configparser import ConfigParser

# Add runtime directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loader import ClusterLoader
from normalizer import ReadingNormalizer
from drift_compensator import DriftCompensator
from correlator import CrossCorrelator
from confidence_scorer import ConfidenceScorer
from matrix_assembler import MatrixAssembler
from calibrator import Calibrator


def run_pipeline(data_dir=None, config_path=None, output_path=None):
    """Execute the full sensor fusion calibration pipeline.

    Args:
        data_dir: Path to cluster data directory. Defaults to ./data/
        config_path: Path to config.ini. Defaults to ./config.ini
        output_path: Path for output JSON. Defaults to stdout.

    Returns:
        Calibration report as a list of records.
    """
    # Resolve default paths
    runtime_dir = os.path.dirname(os.path.abspath(__file__))
    if data_dir is None:
        data_dir = os.path.join(runtime_dir, "data")
    if config_path is None:
        config_path = os.path.join(runtime_dir, "config.ini")

    # Load configuration
    config = ConfigParser()
    config.read(config_path)

    # Stage 1: Load cluster data
    loader = ClusterLoader(data_dir, config_path)
    clusters = loader.load_all()
    cross_ref_map = loader.get_cross_ref_map()

    print(f"Loaded {loader.get_sensor_count()} sensors from "
          f"{len(clusters)} clusters", file=sys.stderr)

    # Stage 2: Normalize readings
    normalizer = ReadingNormalizer()
    for i, cluster in enumerate(clusters):
        clusters[i] = normalizer.normalize_cluster(cluster)

    print(f"Normalization complete. Stats computed for "
          f"{len(normalizer.get_normalization_stats())} sensors", file=sys.stderr)

    # Stage 3: Drift compensation
    compensator = DriftCompensator(config)
    for i, cluster in enumerate(clusters):
        clusters[i] = compensator.compensate_cluster(cluster)

    convergence = compensator.get_convergence_metrics()
    print(f"Drift compensation complete. Avg magnitude: "
          f"{convergence['avg_magnitude']:.6f}", file=sys.stderr)

    # Stage 4: Cross-sensor correlation
    correlator = CrossCorrelator()
    correlation_matrix = correlator.build_correlation_matrix(clusters, cross_ref_map)

    density = correlator.get_matrix_density()
    print(f"Correlation matrix built. Density: {density:.2%}, "
          f"Pairs: {len(correlation_matrix)}", file=sys.stderr)

    # Stage 5: Confidence scoring
    scorer = ConfidenceScorer(config)
    confidence_scores = scorer.score_clusters(clusters, correlation_matrix, cross_ref_map)

    above_threshold = scorer.get_sensors_above_threshold(confidence_scores)
    print(f"Confidence scoring complete. {len(above_threshold)}/"
          f"{len(confidence_scores)} sensors above threshold", file=sys.stderr)

    # Stage 6: Matrix assembly
    assembler = MatrixAssembler(config)
    calibration_matrix = assembler.assemble(clusters, confidence_scores)

    valid, msg = assembler.validate_matrix(calibration_matrix)
    print(f"Matrix assembly complete. Valid: {valid} ({msg})", file=sys.stderr)

    # Stage 7: Final calibration report
    calibrator = Calibrator(config)
    report = calibrator.generate_report(calibration_matrix, confidence_scores, clusters)

    valid, msg = calibrator.validate_report(report)
    print(f"Report generated. Valid: {valid}. Records: {len(report)}", file=sys.stderr)

    # Output
    output_data = {
        "pipeline_version": "2.4.1",
        "sensor_count": len(report),
        "calibration_records": report,
        "summary": calibrator.compute_report_summary(report),
    }

    if output_path:
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Output written to: {output_path}", file=sys.stderr)
    else:
        print(json.dumps(output_data, indent=2))

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sensor Fusion Calibration Pipeline")
    parser.add_argument("--data-dir", help="Path to cluster data directory")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    run_pipeline(
        data_dir=args.data_dir,
        config_path=args.config,
        output_path=args.output,
    )
