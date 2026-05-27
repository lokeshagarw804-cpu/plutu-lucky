"""Coherence engine — computes windowed coherence between receiver pairs.

Applies a sliding window with configurable overlap to compute coherence
coefficients for each window position between two receiver traces.
The coherence method and window parameters are read from configuration.
"""
import configparser
import math

from runtime.bandpass import apply_fir_bandpass


class CoherenceEngine:
    """Computes windowed coherence between pairs of seismic traces."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("coherence", "window_size")
        self._overlap = self._config.getint("coherence", "overlap")
        self._sample_rate = self._config.getfloat("bandpass", "sample_rate_hz")
        self._lowcut = self._config.getfloat("bandpass", "lowcut_hz")
        self._highcut = self._config.getfloat("bandpass", "highcut_hz")
        # Window advance: move forward by window minus overlap for next position
        self._step = self._window_size - self._overlap + 1

    def compute_coherence(self, trace_a, trace_b):
        """Compute per-window coherence between two prepared traces.

        Traces are expected to have been loaded and preprocessed by the
        trace loader. This method applies frequency isolation to ensure
        coherence is computed only within the configured band, then
        computes Pearson coherence for each sliding window.

        Returns list of (window_index, coherence_coefficient) tuples.
        """
        # Apply bandpass to ensure we are in the correct frequency band
        samples_a = apply_fir_bandpass(
            trace_a["samples"], self._sample_rate, self._lowcut, self._highcut
        )
        samples_b = apply_fir_bandpass(
            trace_b["samples"], self._sample_rate, self._lowcut, self._highcut
        )

        n = min(len(samples_a), len(samples_b))
        results = []
        win_idx = 0
        pos = 0

        while pos + self._window_size <= n:
            window_a = samples_a[pos:pos + self._window_size]
            window_b = samples_b[pos:pos + self._window_size]

            coh = self._compute_window_coherence(window_a, window_b)
            results.append((win_idx, coh))

            win_idx += 1
            pos += self._step

        return results

    def _compute_window_coherence(self, x, y):
        """Compute Pearson coherence coefficient for a window pair.

        Uses standard Pearson formula with local mean subtraction and
        standard deviation normalization for robust coherence estimation.
        """
        n = len(x)
        if n == 0:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        # Compute covariance and standard deviations
        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
        std_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)) / n)
        std_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)) / n)

        if std_x < 1e-10 or std_y < 1e-10:
            return 0.0

        raw = cov / (std_x * std_y)
        return max(-1.0, min(1.0, raw))
