"""
Anomaly event detector.

Identifies anomalous readings based on statistical deviation from
the station mean within each processing window. Events are flagged
when the deviation exceeds the configured noise threshold.

Detected anomalies are reported with a severity score indicating
the magnitude of deviation relative to the threshold.
"""

import configparser
from collections import defaultdict


class EventDetector:
    """Detects anomalous signal events."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._noise_threshold = config.getfloat(
            "detection", "noise_threshold"
        )
        self._window_size = config.getint("detection", "window_size")
        self._min_readings = config.getint(
            "detection", "min_readings_per_window"
        )

    def detect_anomalies(self, calibrated_readings, windows):
        """Detect anomalous readings across processing windows.

        For each window, computes per-station mean and flags readings
        that deviate beyond the noise threshold.
        """
        anomalies = []

        for window in windows:
            start, end = window
            window_readings = [
                r for r in calibrated_readings
                if start <= r["timestamp"] <= end
            ]

            station_groups = defaultdict(list)
            for r in window_readings:
                station_groups[r["station_id"]].append(r)

            for station_id, readings in station_groups.items():
                if len(readings) < self._min_readings:
                    continue

                values = [r["calibrated_value"] for r in readings]
                mean_val = sum(values) / len(values)
                std_val = (
                    sum((v - mean_val) ** 2 for v in values) / len(values)
                ) ** 0.5

                if std_val == 0:
                    continue

                for reading in readings:
                    deviation = abs(
                        reading["calibrated_value"] - mean_val
                    ) / std_val
                    if deviation > self._noise_threshold:
                        severity = round(deviation / self._noise_threshold, 4)
                        anomalies.append({
                            "reading_id": reading["reading_id"],
                            "station_id": reading["station_id"],
                            "timestamp": reading["timestamp"],
                            "channel": reading["channel"],
                            "calibrated_value": reading["calibrated_value"],
                            "deviation": round(deviation, 4),
                            "severity_score": severity,
                        })

        return anomalies
