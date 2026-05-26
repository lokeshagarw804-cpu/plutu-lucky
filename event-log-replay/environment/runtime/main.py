"""Main entry point — orchestrates log replay pipeline."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.loader import LogLoader
from runtime.causality import CausalityChecker
from runtime.reporter import AnomalyReporter


def main():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    loader = LogLoader(config_path)
    events = loader.load_and_merge()

    checker = CausalityChecker(config_path)
    violations = checker.detect_violations(events)

    reporter = AnomalyReporter(config_path)
    anomalies, summary = reporter.generate_report(violations, events)

    with open(os.path.join(output_dir, "anomalies.json"), "w") as f:
        json.dump(anomalies, f, indent=2)

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Pipeline complete: {summary['total_violations']} violations, "
          f"{summary['total_anomalies']} anomalies reported.")


if __name__ == "__main__":
    main()
