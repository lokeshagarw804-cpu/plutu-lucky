"""Signal anomaly detection — main entry point."""
import json
import os

from runtime.ingest import SensorIngest
from runtime.smoother import WindowSmoother
from runtime.spectrum import SpectrumAnalyzer
from runtime.detector import AnomalyDetector


def main():
    config_path = "/app/runtime/config.ini"

    ingest = SensorIngest(config_path)
    readings = ingest.load_all()

    smoother = WindowSmoother(config_path)
    smoothed = smoother.apply(readings)

    analyzer = SpectrumAnalyzer(config_path)
    features = analyzer.compute_features(smoothed)

    detector = AnomalyDetector(config_path)
    anomalies, summary = detector.detect(features)

    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "anomalies.json"), "w") as f:
        json.dump(anomalies, f, indent=2)

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
