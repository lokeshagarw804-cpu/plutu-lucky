"""Flow meter calibration pipeline — main entry point.

Orchestrates the full calibration workflow: load sensor data, apply
polynomial calibration curves, compensate for temperature, aggregate
into intervals, and generate compliance reports.
"""
import json
import os

from runtime.loader import MeterLoader
from runtime.calibrator import FlowCalibrator
from runtime.compensator import TempCompensator
from runtime.aggregator import IntervalAggregator
from runtime.reporter import ComplianceReporter


def main():
    config_path = "/app/runtime/config.ini"

    # Stage 1: Load meter data
    loader = MeterLoader(config_path)
    meters = loader.load_meters()

    # Stage 2: Apply calibration polynomial
    calibrator = FlowCalibrator(config_path)
    calibrated = calibrator.calibrate_readings(meters)

    # Stage 3: Temperature compensation
    compensator = TempCompensator(config_path)
    compensated = compensator.compensate(calibrated)

    # Stage 4: Interval aggregation
    aggregator = IntervalAggregator(config_path)
    aggregated = aggregator.aggregate(compensated)

    # Stage 5: Compliance reporting
    reporter = ComplianceReporter(config_path)
    report = reporter.generate_report(aggregated)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "calibration_results.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Write interval summary
    summary = {
        "total_meters": report["total_meters"],
        "compliant_count": report["compliant_count"],
        "non_compliant_count": report["non_compliant_count"],
        "meter_order": report["meter_order"],
        "total_readings_processed": sum(
            sum(iv["reading_count"] for iv in intervals)
            for intervals in aggregated.values()
        ),
        "total_intervals": sum(
            len(intervals) for intervals in aggregated.values()
        ),
    }
    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
