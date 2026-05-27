"""Anomaly detector — identifies sustained anomaly events.

Examines per-window metrics to find consecutive windows where
anomaly scores exceed configured thresholds. Generates alert
objects for sustained anomaly periods.
"""
import configparser


class AnomalyDetector:
    """Detects sustained anomaly events from windowed metrics."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._min_consecutive = self._config.getint("scoring", "min_consecutive")
        self._speed_threshold = self._config.getfloat("anomaly", "speed_threshold")
        self._fuel_drop_rate = self._config.getfloat("anomaly", "fuel_drop_rate")
        self._temp_ceiling = self._config.getfloat("anomaly", "temp_ceiling")

    def detect_anomalies(self, vehicle_id, windows):
        """Detect sustained anomaly events for a vehicle.

        An event is a run of consecutive windows where at least one
        anomaly metric is flagged. Returns list of alert dicts.
        """
        alerts = []
        run_start = None
        run_length = 0
        run_metrics = []

        for w in windows:
            is_anomalous = self._check_window(w)
            if is_anomalous:
                if run_start is None:
                    run_start = w["window_idx"]
                run_length += 1
                run_metrics.append(w)
            else:
                if run_length >= self._min_consecutive:
                    alerts.append(self._build_alert(
                        vehicle_id, run_start, run_length, run_metrics
                    ))
                run_start = None
                run_length = 0
                run_metrics = []

        # Check final run
        if run_length >= self._min_consecutive:
            alerts.append(self._build_alert(
                vehicle_id, run_start, run_length, run_metrics
            ))

        return alerts

    def _check_window(self, w):
        """Determine if a window exhibits anomalous behavior.

        Window is anomalous if it has speed spikes, excessive fuel
        consumption, or thermal deviation above zero.
        """
        if w["speed_spikes"] > 0:
            return True
        if w["fuel_consumption"] > self._fuel_drop_rate:
            return True
        if w["thermal_deviation"] > 0:
            return True
        return False

    def _build_alert(self, vehicle_id, start_idx, length, metrics):
        """Construct an alert object from a run of anomalous windows."""
        total_spikes = sum(m["speed_spikes"] for m in metrics)
        max_fuel = max(m["fuel_consumption"] for m in metrics)
        max_thermal = max(m["thermal_deviation"] for m in metrics)

        return {
            "vehicle_id": vehicle_id,
            "start_window": start_idx,
            "end_window": start_idx + length - 1,
            "duration_windows": length,
            "total_speed_spikes": total_spikes,
            "max_fuel_consumption": round(max_fuel, 4),
            "max_thermal_deviation": round(max_thermal, 4),
        }
