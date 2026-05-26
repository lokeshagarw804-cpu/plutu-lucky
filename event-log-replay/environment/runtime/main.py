"""Event log replay engine — main entry point.

Reads distributed event logs from service nodes, merges by
timestamp windows, checks causal ordering via vector clocks,
and outputs anomaly reports.
"""
import json
import os

from runtime.loader import LogLoader
from runtime.causality import CausalityChecker
from runtime.reporter import AnomalyReporter


def main():
    config_path = "/app/runtime/config.ini"

    loader = LogLoader(config_path)
    events = loader.load_and_merge()

    checker = CausalityChecker(config_path)
    violations = checker.detect_violations(events)

    reporter = AnomalyReporter(config_path)
    anomalies, summary = reporter.generate_report(violations, events)

    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "anomalies.json"), "w") as f:
        json.dump(anomalies, f, indent=2)

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
