"""Window aggregator — groups z-scores into fixed-size time windows.

Slides a window of configurable size across the sorted z-score stream,
computing the maximum absolute z-score per window. Windows are defined
as [window_start, window_start + window_size) — left-inclusive,
right-exclusive.

A window is only emitted if it contains at least min_readings data points.
"""
import configparser


class WindowAggregator:
    """Groups scored readings into time windows and picks peak z-score."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("windows", "window_size")
        self._min_readings = self._config.getint("windows", "min_readings")

    def aggregate(self, scored_readings):
        """Aggregate scored readings into time windows.

        Args:
            scored_readings: list of (timestamp, z_score) sorted by time

        Returns:
            list of dicts with keys: window_start, window_end, peak_z,
            reading_count
        """
        if not scored_readings:
            return []

        first_ts = scored_readings[0][0]
        windows = []
        current_start = first_ts
        current_readings = []

        for ts, z_score in scored_readings:
            # Check if reading belongs to next window
            while ts - current_start > self._window_size:
                # Emit current window if enough readings
                if len(current_readings) >= self._min_readings:
                    peak = max(abs(z) for z in current_readings)
                    windows.append({
                        "window_start": current_start,
                        "window_end": current_start + self._window_size,
                        "peak_z": round(peak, 4),
                        "reading_count": len(current_readings),
                    })
                current_readings = []
                current_start += self._window_size

            current_readings.append(z_score)

        # Emit final window
        if len(current_readings) >= self._min_readings:
            peak = max(abs(z) for z in current_readings)
            windows.append({
                "window_start": current_start,
                "window_end": current_start + self._window_size,
                "peak_z": round(peak, 4),
                "reading_count": len(current_readings),
            })

        return windows
