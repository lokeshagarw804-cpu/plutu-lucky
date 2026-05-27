"""Fleet telemetry monitor — main entry point.

Orchestrates the full anomaly detection pipeline: load vehicle data,
compute windowed metrics, detect sustained anomalies, score severity,
and generate the alert report.
"""
from runtime.loader import FleetLoader
from runtime.analyzer import TelemetryAnalyzer
from runtime.detector import AnomalyDetector
from runtime.scorer import SeverityScorer
from runtime.reporter import ReportGenerator


def main():
    config_path = "/app/runtime/config.ini"

    # Load fleet data
    loader = FleetLoader(config_path)
    vehicles = loader.load_vehicles()

    # Analyze each vehicle
    analyzer = TelemetryAnalyzer(config_path)
    detector = AnomalyDetector(config_path)

    all_alerts = []
    vehicle_ids = sorted(vehicles.keys())

    for vid in vehicle_ids:
        windows = analyzer.analyze_vehicle(vehicles[vid])
        alerts = detector.detect_anomalies(vid, windows)
        all_alerts.extend(alerts)

    # Score alerts
    scorer = SeverityScorer(config_path)
    scored_alerts = scorer.score_alerts(all_alerts)

    # Generate report
    reporter = ReportGenerator(config_path)
    reporter.generate(scored_alerts)


if __name__ == "__main__":
    main()
