"""Sensor fusion — combines per-sensor anomaly windows into vehicle score.

Each sensor has a configured weight reflecting its diagnostic importance.
The fused score for a time window combines per-sensor peak z-scores
weighted by these factors.
"""
import configparser


class SensorFusion:
    """Fuses per-sensor window scores into a single vehicle anomaly score."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_sensors = self._config.get("sensors", "active")
        self._sensors = [s.strip() for s in raw_sensors.split(",")]
        self._weights = {}
        for sensor in self._sensors:
            self._weights[sensor] = self._config.getfloat(
                "sensors", f"weight_{sensor}"
            )
        self._window_size = self._config.getint("windows", "window_size")

    def fuse(self, sensor_windows):
        """Fuse per-sensor window data into vehicle-level scores.

        Args:
            sensor_windows: dict {sensor_name: [window_dicts]}

        Returns:
            list of dicts with keys: window_start, window_end, fused_score,
            sensors_reporting
        """
        # Collect all unique window start times
        all_starts = set()
        by_start = {}
        for sensor, windows in sensor_windows.items():
            for w in windows:
                start = w["window_start"]
                all_starts.add(start)
                if start not in by_start:
                    by_start[start] = {}
                by_start[start][sensor] = w

        fused_results = []
        for start in sorted(all_starts):
            sensor_data = by_start[start]
            total_score = 0.0
            n_sensors = 0

            for sensor, w in sensor_data.items():
                weight = self._weights.get(sensor, 1.0)
                total_score += weight * w["peak_z"]
                n_sensors += 1

            # Compute weighted average
            fused_score = total_score / n_sensors if n_sensors > 0 else 0.0

            fused_results.append({
                "window_start": start,
                "window_end": start + 5,
                "fused_score": round(fused_score, 4),
                "sensors_reporting": n_sensors,
            })

        return fused_results
