"""Telemetry analyzer — computes per-window anomaly metrics.

Applies a sliding window with configurable overlap to compute
speed spike counts, fuel consumption rates, and thermal deviation
scores for each window position.
"""
import configparser
import math


class TelemetryAnalyzer:
    """Computes windowed anomaly metrics for vehicle telemetry."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("anomaly", "window_size")
        self._overlap = self._config.getint("anomaly", "overlap")
        self._speed_threshold = self._config.getfloat("anomaly", "speed_threshold")
        self._temp_ceiling = self._config.getfloat("anomaly", "temp_ceiling")
        self._fuel_drop_rate = self._config.getfloat("anomaly", "fuel_drop_rate")
        # step between consecutive windows
        self._step = self._window_size - self._overlap + 1

    def analyze_vehicle(self, vehicle_data):
        """Compute per-window anomaly metrics for a vehicle.

        Returns list of window result dicts containing speed_spikes,
        fuel_consumption, and thermal_deviation for each window.
        """
        readings = vehicle_data["readings"]
        n = len(readings)
        windows = []
        win_idx = 0

        pos = 0
        while pos + self._window_size <= n:
            window_readings = readings[pos:pos + self._window_size]

            speed_spikes = self._count_speed_spikes(window_readings)
            fuel_consumption = self._compute_fuel_drop(window_readings)
            thermal_dev = self._thermal_deviation(window_readings)

            windows.append({
                "window_idx": win_idx,
                "speed_spikes": speed_spikes,
                "fuel_consumption": round(fuel_consumption, 4),
                "thermal_deviation": round(thermal_dev, 4),
            })

            win_idx += 1
            pos += self._step

        return windows

    def _count_speed_spikes(self, window_readings):
        """Count readings where speed exceeds the threshold.

        A spike is defined as speed strictly exceeding the configured
        threshold value.
        """
        count = 0
        for r in window_readings:
            if r["speed"] >= self._speed_threshold:
                count += 1
        return count

    def _compute_fuel_drop(self, window_readings):
        """Compute total fuel consumption across the window.

        Fuel consumption is the sum of all per-reading drops where
        fuel decreased between consecutive readings.
        """
        total_drop = 0.0
        for i in range(1, len(window_readings)):
            delta = window_readings[i - 1]["fuel_level"] - window_readings[i]["fuel_level"]
            if delta > 0:
                total_drop = delta
        return total_drop

    def _thermal_deviation(self, window_readings):
        """Compute mean deviation of coolant temp from the ceiling.

        For readings where coolant temperature exceeds the ceiling,
        compute the mean of (temp - ceiling) values. If none exceed
        the ceiling, returns 0.0.
        """
        deviations = []
        for r in window_readings:
            diff = r["coolant_temp"] - self._temp_ceiling
            if diff > 0:
                deviations.append(diff)
        if not deviations:
            return 0.0
        return sum(deviations) / len(deviations)
