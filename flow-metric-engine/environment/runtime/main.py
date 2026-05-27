"""Flow metric engine — main entry point.

Orchestrates the full traffic analysis pipeline: load packet captures,
compute bandwidth and latency metrics per interface, build traffic
matrix, and detect anomalous flows.
"""
import json
import os

from runtime.loader import PacketLoader
from runtime.bandwidth import BandwidthCalculator
from runtime.latency import LatencyAnalyzer
from runtime.matrix import TrafficMatrix
from runtime.anomaly import AnomalyDetector


def main():
    config_path = "/app/runtime/config.ini"

    # Load packet data
    loader = PacketLoader(config_path)
    interfaces = loader.load_interfaces()

    # Compute per-interface metrics
    bw_calc = BandwidthCalculator(config_path)
    lat_calc = LatencyAnalyzer(config_path)

    bw_results = {}
    lat_results = {}

    for iface_id, data in interfaces.items():
        bw_results[iface_id] = bw_calc.compute(data)
        lat_results[iface_id] = lat_calc.compute(data)

    # Build traffic matrix
    matrix_builder = TrafficMatrix()
    matrix = matrix_builder.build(interfaces, bw_results, lat_results)

    # Detect anomalies
    detector = AnomalyDetector(config_path)
    anomalies = detector.detect(interfaces, bw_results, lat_results)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "traffic_matrix.json"), "w") as f:
        json.dump(matrix, f, indent=2)

    anomaly_output = {
        "threshold": detector._threshold,
        "min_consecutive_windows": detector._min_consecutive,
        "total_anomalies": len(anomalies),
        "anomalies": anomalies,
    }
    with open(os.path.join(output_dir, "anomaly_report.json"), "w") as f:
        json.dump(anomaly_output, f, indent=2)


if __name__ == "__main__":
    main()
