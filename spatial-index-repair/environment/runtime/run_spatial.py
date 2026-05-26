"""Signal correlation engine — main entry point.

Orchestrates the full correlation analysis: load station data, normalize
signals, align pairs, compute windowed correlations, build correlation
matrix, and detect significant events.
"""
import json
import os
from itertools import combinations

from runtime.loader import SignalLoader
from runtime.normalizer import SignalNormalizer
from runtime.aligner import SignalAligner
from runtime.correlator import WindowedCorrelator
from runtime.matrix_builder import MatrixBuilder
from runtime.event_detector import EventDetector


def main():
    config_path = "/app/runtime/config.ini"

    # Load and normalize
    loader = SignalLoader(config_path)
    raw_stations = loader.load_stations()

    normalizer = SignalNormalizer()
    stations = normalizer.normalize(raw_stations)

    # Align and correlate all pairs
    aligner = SignalAligner()
    correlator = WindowedCorrelator(config_path)

    station_ids = sorted(stations.keys())
    pair_correlations = {}

    for id_a, id_b in combinations(station_ids, 2):
        aligned_a, aligned_b, overlap = aligner.align_pair(
            stations[id_a], stations[id_b]
        )
        if overlap > 0:
            windows = correlator.correlate(aligned_a, aligned_b)
            pair_correlations[(id_a, id_b)] = windows
        else:
            pair_correlations[(id_a, id_b)] = []

    # Build matrix
    builder = MatrixBuilder()
    matrix_result = builder.build_matrix(stations, pair_correlations)

    # Detect events
    detector = EventDetector(config_path)
    events = detector.detect_events(pair_correlations)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "correlation_matrix.json"), "w") as f:
        json.dump(matrix_result, f, indent=2)

    event_output = {
        "threshold": 0.75,
        "min_duration_windows": 2,
        "total_events": len(events),
        "events": events,
    }
    with open(os.path.join(output_dir, "detected_events.json"), "w") as f:
        json.dump(event_output, f, indent=2)


if __name__ == "__main__":
    main()
