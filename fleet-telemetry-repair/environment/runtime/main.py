"""Fleet telemetry anomaly detection — main entry point.

Orchestrates the full pipeline: load vehicle telemetry, compute per-sensor
anomaly scores, aggregate into time windows, fuse sensor scores, classify
severity, and generate the final report.
"""
from runtime.loader import TelemetryLoader
from runtime.scorer import AnomalyScorer
from runtime.aggregator import WindowAggregator
from runtime.fusion import SensorFusion
from runtime.classifier import SeverityClassifier
from runtime.reporter import ReportGenerator


def main():
    config_path = "/app/runtime/config.ini"

    # Stage 1: Load fleet telemetry
    loader = TelemetryLoader(config_path)
    fleet_data = loader.load_fleet()

    # Stage 2-5: Process each vehicle
    scorer = AnomalyScorer(config_path)
    aggregator = WindowAggregator(config_path)
    fusion = SensorFusion(config_path)
    classifier = SeverityClassifier(config_path)

    fleet_anomalies = {}

    for vehicle_id, sensors in fleet_data.items():
        # Score each sensor independently
        sensor_windows = {}
        for sensor_name, readings in sensors.items():
            scored = scorer.score_sensor(readings)
            windows = aggregator.aggregate(scored)
            sensor_windows[sensor_name] = windows

        # Fuse sensor scores
        fused = fusion.fuse(sensor_windows)

        # Classify severity
        anomalies = classifier.classify(fused)
        fleet_anomalies[vehicle_id] = anomalies

    # Stage 6: Generate report
    output_dir = "/app/runtime/output"
    reporter = ReportGenerator(output_dir)
    reporter.generate(fleet_anomalies)


if __name__ == "__main__":
    main()
