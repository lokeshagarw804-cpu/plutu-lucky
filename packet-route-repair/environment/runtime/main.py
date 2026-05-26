"""Packet route analyzer — main entry point.

Loads network packet logs from router nodes, computes shortest-path
routing costs, detects routing anomalies (loops, suboptimal paths),
and generates flow quality reports.
"""
import json
import os

from runtime.ingest import PacketIngestor
from runtime.router import RoutingEngine
from runtime.tracker import AnomalyTracker
from runtime.reporter import FlowReporter


def main():
    config_path = "/app/runtime/config.ini"

    ingestor = PacketIngestor(config_path)
    packets = ingestor.load_all()

    engine = RoutingEngine(config_path)
    engine.build_graph(packets)
    optimal_costs = engine.compute_optimal_costs()

    tracker = AnomalyTracker(config_path)
    analysis = tracker.analyze_packets(packets, optimal_costs)

    reporter = FlowReporter(config_path)
    flows, summary = reporter.generate_report(analysis)

    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "flows.json"), "w") as f:
        json.dump(flows, f, indent=2)

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
