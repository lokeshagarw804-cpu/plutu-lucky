#!/usr/bin/env python3
"""
Entry point for the telemetry batch reconciler.
Outputs results to /output/reconciliation_report.json
"""
import json
import os
import sys

# Add parent to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.reconciler import reconcile


def main():
    output_dir = "/output"
    os.makedirs(output_dir, exist_ok=True)

    result = reconcile()

    output_path = os.path.join(output_dir, "reconciliation_report.json")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Report written to {output_path}")
    print(f"Batches processed: {len(result['batch_summaries'])}")
    print(f"Stations: {len(result['station_totals'])}")

    # Print summary
    for st in result["station_totals"]:
        print(f"  {st['station']}: {st['total_events']} events, "
              f"mean={st['overall_mean']}")


if __name__ == "__main__":
    main()
