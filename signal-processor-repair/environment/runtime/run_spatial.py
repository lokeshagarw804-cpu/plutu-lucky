"""
Main entry point for the signal processing system.

Orchestrates the full processing flow:
1. Load sensor readings from station data files
2. Normalize readings with station calibration offsets
3. Create temporal processing windows
4. Compute cross-station correlations
5. Detect anomalous signal events
6. Generate output reports
"""

from runtime.loader import load_readings
from runtime.normalizer import SignalNormalizer
from runtime.aligner import TemporalAligner
from runtime.correlator import Correlator
from runtime.event_detector import EventDetector
from runtime.matrix_builder import MatrixBuilder


def main():
    """Run the signal processing system."""
    # Stage 1: Load sensor data
    readings = load_readings()

    # Stage 2: Apply calibration
    normalizer = SignalNormalizer()
    calibrated = normalizer.calibrate_readings(readings)

    # Stage 3: Create windows
    aligner = TemporalAligner()
    windows = aligner.create_windows(calibrated)

    # Stage 4: Compute correlations
    correlator = Correlator()
    correlation_matrix = correlator.compute_correlations(calibrated, windows)

    # Stage 5: Detect anomalies
    detector = EventDetector()
    anomalies = detector.detect_anomalies(calibrated, windows)

    # Stage 6: Generate reports
    builder = MatrixBuilder()
    anomaly_report, corr_report, summary = builder.generate_reports(
        calibrated, anomalies, correlation_matrix, windows
    )

    print(f"Processed {summary['total_readings']} readings")
    print(f"Stations: {summary['stations_processed']}")
    print(f"Windows: {summary['windows_created']}")
    print(f"Anomalies: {summary['total_anomalies']}")
    print(f"Correlation pairs: {summary['correlation_pairs']}")


if __name__ == "__main__":
    main()
