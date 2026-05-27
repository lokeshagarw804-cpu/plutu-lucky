"""Rolling aggregator — computes windowed statistics over gradient series.

Applies a sliding window to compute mean gradient magnitude, peak values,
and variance within each window. Window boundaries determine how many
samples contribute to each aggregate value.
"""
import configparser
import math


class RollingAggregator:
    """Computes windowed aggregate statistics over pressure gradients."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("gradient", "window_size")
        self._overlap = self._config.getint("gradient", "overlap")
        self._step = self._window_size - self._overlap

    def aggregate(self, gradients):
        """Compute rolling window statistics for gradient time-series.

        For each window position, computes:
        - mean_magnitude: average of absolute gradient values in window
        - peak_value: maximum absolute gradient in window
        - variance: variance of gradient values in window

        Returns dict mapping segment_id to list of window aggregates.
        """
        aggregated = {}

        for seg_id, grad_data in gradients.items():
            grad_values = grad_data["gradient_values"]
            n = len(grad_values)
            windows = []
            win_idx = 0

            pos = 0
            while pos + self._window_size <= n:
                # BUG: uses range(pos, pos + self._window_size - 1) 
                # which gives window_size - 1 elements instead of window_size
                # Should be range(pos, pos + self._window_size) for full window
                window_data = [grad_values[k] for k in range(pos, pos + self._window_size - 1)]

                # Compute statistics
                magnitudes = [abs(v) for v in window_data]
                mean_mag = sum(magnitudes) / len(magnitudes) if magnitudes else 0.0
                peak_val = max(magnitudes) if magnitudes else 0.0
                
                mean_grad = sum(window_data) / len(window_data) if window_data else 0.0
                variance = (
                    sum((v - mean_grad) ** 2 for v in window_data) / len(window_data)
                    if window_data else 0.0
                )

                windows.append({
                    "window_index": win_idx,
                    "start_sample": pos,
                    "end_sample": pos + self._window_size - 1,
                    "mean_magnitude": round(mean_mag, 6),
                    "peak_value": round(peak_val, 6),
                    "variance": round(variance, 6),
                    "mean_gradient": round(mean_grad, 6),
                })

                win_idx += 1
                pos += self._step

            aggregated[seg_id] = {
                "segment_id": seg_id,
                "windows": windows,
                "total_windows": len(windows),
            }

        return aggregated
