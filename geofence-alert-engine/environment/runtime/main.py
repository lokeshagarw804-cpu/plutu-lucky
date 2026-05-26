"""Geofence alert engine — main entry point.

Loads vehicle GPS telemetry from fleet feeds, merges readings within
time windows, evaluates geofence containment, tracks dwell state,
and generates severity-ranked alert reports.
"""
import json
import os

from runtime.loader import FleetLoader
from runtime.geofence import GeofenceEvaluator
from runtime.tracker import DwellTracker
from runtime.alerts import AlertGenerator


def main():
    config_path = "/app/runtime/config.ini"

    loader = FleetLoader(config_path)
    readings = loader.load_and_merge()

    evaluator = GeofenceEvaluator(config_path)
    containment = evaluator.evaluate_all(readings)

    tracker = DwellTracker(config_path)
    dwell_data = tracker.compute_dwells(containment)

    generator = AlertGenerator(config_path)
    alerts, summary = generator.generate(dwell_data)

    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "alerts.json"), "w") as f:
        json.dump(alerts, f, indent=2)

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
