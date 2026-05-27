"""Flow metric engine — main entry point.

Orchestrates the traffic analysis pipeline: load flows, classify
packets, aggregate into windows, score risk, and report violations.
"""
import json
import os

from runtime.loader import FlowLoader
from runtime.classifier import PacketClassifier
from runtime.aggregator import WindowAggregator
from runtime.scorer import FlowScorer
from runtime.reporter import ViolationReporter


def main():
    config_path = "/app/runtime/config.ini"

    loader = FlowLoader(config_path)
    flows = loader.load()

    classifier = PacketClassifier(config_path)
    aggregator = WindowAggregator(config_path)
    scorer = FlowScorer(config_path)

    flow_scores = {}
    flow_classifications = {}

    for flow_id, flow_data in flows.items():
        labels = classifier.classify_flow(flow_data)
        windows = aggregator.aggregate(labels, flow_data)
        scored = scorer.score_windows(windows)
        flow_scores[flow_id] = scored
        flow_classifications[flow_id] = labels

    reporter = ViolationReporter(config_path)
    report = reporter.report(flow_scores)

    # Build classification summary
    raw_cats = "small,medium,large"
    categories = [c.strip() for c in raw_cats.split(",")]
    classification_summary = {}
    for flow_id, labels in flow_classifications.items():
        counts = {cat: labels.count(cat) for cat in categories}
        classification_summary[flow_id] = counts

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "violation_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    with open(os.path.join(output_dir, "classification_summary.json"), "w") as f:
        json.dump(classification_summary, f, indent=2)


if __name__ == "__main__":
    main()
