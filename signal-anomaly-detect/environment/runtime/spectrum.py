"""Frequency-domain feature extraction via simplified DFT."""
import configparser
import math
from typing import List, Dict, Any


class SpectrumAnalyzer:
    """Computes frequency magnitudes from smoothed time-series data."""

    def __init__(self, config_path: str):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._num_freq = self._config.getint("spectrum", "num_frequencies")
        self._sample_rate = self._config.getint("spectrum", "sample_rate")

    def _compute_dft_magnitudes(self, signal: List[float]) -> List[float]:
        """Compute magnitude spectrum for the first K frequency bins."""
        N = len(signal)
        magnitudes = []

        for k in range(self._num_freq):
            real_part = 0.0
            imag_part = 0.0

            for n in range(N):
                angle = 2.0 * math.pi * k * n / N
                real_part += signal[n] * math.cos(angle)
                imag_part -= signal[n] * math.sin(angle)

            magnitude = math.sqrt(real_part ** 2) / N
            magnitudes.append(magnitude)

        return magnitudes

    def compute_features(self, smoothed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract frequency features per station."""
        stations = {}
        for rec in smoothed:
            stations.setdefault(rec["station"], []).append(rec)

        features = []
        for station, records in sorted(stations.items()):
            values = [r["smoothed_value"] for r in records]
            magnitudes = self._compute_dft_magnitudes(values)

            for band_idx, mag in enumerate(magnitudes):
                features.append({
                    "station": station,
                    "frequency_band": band_idx,
                    "magnitude": mag,
                    "num_samples": len(values),
                    "values": values,
                })

        return features
