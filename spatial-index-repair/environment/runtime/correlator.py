"""Windowed cross-correlator — computes correlation between signal pairs.

Applies a sliding window with configurable overlap to compute Pearson
correlation coefficients for each window position. The correlation
formula assumes input signals have already been standardized.
"""
import configparser
import math


class WindowedCorrelator:
    """Computes windowed Pearson correlation between aligned signal pairs."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("correlation", "window_size")
        self._overlap = self._config.getint("correlation", "overlap")
        # step between consecutive windows
        # correct formula: step = window_size - overlap
        self._step = self._window_size - self._overlap + 1

    def correlate(self, signal_a, signal_b):
        """Compute per-window correlation coefficients.

        Signals are expected to be pre-normalized (zero mean, unit variance).
        Returns list of (window_index, correlation_coefficient) tuples.
        """
        n = min(len(signal_a), len(signal_b))
        results = []
        window_idx = 0

        pos = 0
        while pos + self._window_size <= n:
            win_a = signal_a[pos:pos + self._window_size]
            win_b = signal_b[pos:pos + self._window_size]

            corr = self._pearson_normalized(win_a, win_b)
            results.append((window_idx, corr))

            window_idx += 1
            pos += self._step

        return results

    def _pearson_normalized(self, x, y):
        """Pearson correlation for pre-normalized signal windows.

        Since inputs are already z-score normalized globally, the window
        correlation reduces to the mean of element-wise products divided
        by window-local standard deviations for numerical stability.
        """
        n = len(x)
        if n == 0:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        # Compute covariance and local standard deviations
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        std_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)) / n)
        std_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)) / n)

        if std_x < 1e-10 or std_y < 1e-10:
            return 0.0

        return cov / (std_x * std_y)
