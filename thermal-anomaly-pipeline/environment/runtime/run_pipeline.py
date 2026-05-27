#!/usr/bin/env python3
"""
Thermal Anomaly Detection Pipeline - Main Entry Point.

Processes sensor readings from multiple thermal monitoring zones,
detects anomalies via sliding window analysis, scores their severity,
correlates cross-zone events, and produces prioritized alert batches.

Usage:
    python run_pipeline.py [--data-dir DATA_DIR] [--output OUTPUT_FILE]
"""
import sys
import os
import json
import argparse
import configparser

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loader import load_zone_data, get_zone_metadata
from window_processor import process_windows, detect_threshold_breaches
from anomaly_scorer import score_breaches
from correlator import correlate_zones
from alert_builder import build_alert_batch


def load_config(config_path: str) -> configparser.ConfigParser:
    """Load pipeline configuration."""
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def run_pipeline(data_dir: str, config_path: str) -> dict:
    """
    Execute the full anomaly detection pipeline.
    Returns the final alert batch as a dict.
    """
    config = load_config(config_path)
    correlation_window = config.getint('pipeline', 'correlation_window', fallback=30)
    max_batch_size = config.getint('pipeline', 'max_batch_size', fallback=50)
    min_alert_score = config.getfloat('scoring', 'min_alert_score', fallback=25.0)

    # Phase 1: Load sensor data
    zone_data = load_zone_data(data_dir)
    zone_metadata = get_zone_metadata(data_dir)

    # Phase 2: Process windows and detect breaches per zone
    zone_breaches = {}
    pipeline_stats = {
        'zones_processed': 0,
        'total_windows': 0,
        'total_breaches': 0,
    }

    for zone_id in sorted(zone_data.keys()):
        readings = zone_data[zone_id]
        meta = zone_metadata[zone_id]

        # Sliding window processing
        windows = process_windows(readings, meta['window_size'])
        pipeline_stats['total_windows'] += len(windows)

        # Threshold breach detection
        breaches = detect_threshold_breaches(
            windows, meta['threshold_high'], meta['threshold_critical']
        )

        # Score breaches
        scored_breaches = score_breaches(
            breaches, meta['threshold_high'], meta['threshold_critical'],
            meta['weight_factors']
        )

        # Filter by minimum score
        filtered = [b for b in scored_breaches if b['final_score'] >= min_alert_score]

        if filtered:
            zone_breaches[zone_id] = filtered

        pipeline_stats['total_breaches'] += len(filtered)
        pipeline_stats['zones_processed'] += 1

    # Phase 3: Cross-zone correlation
    correlated_events = correlate_zones(zone_breaches, correlation_window)

    # Phase 4: Build alert batch
    alert_batch = build_alert_batch(correlated_events, max_batch_size)

    # Add pipeline metadata
    result = {
        'pipeline_stats': pipeline_stats,
        'correlation_summary': {
            'total_correlated_events': len(correlated_events),
            'pre_correlation_breaches': pipeline_stats['total_breaches'],
        },
        'alert_batch': alert_batch,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='Thermal Anomaly Detection Pipeline')
    parser.add_argument('--data-dir', default=os.path.join(os.path.dirname(__file__), 'data'),
                        help='Path to sensor data directory')
    parser.add_argument('--config', default=os.path.join(os.path.dirname(__file__), 'config.ini'),
                        help='Path to configuration file')
    parser.add_argument('--output', default=None, help='Output file path (stdout if not specified)')
    args = parser.parse_args()

    result = run_pipeline(args.data_dir, args.config)

    output_json = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"Results written to {args.output}")
    else:
        print(output_json)


if __name__ == '__main__':
    main()
