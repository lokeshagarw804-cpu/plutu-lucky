"""Trace loader — reads seismic receiver waveforms and prepares them.

Loads raw waveform samples from receiver JSON files, applies instrument
response correction via bandpass filtering, and whitens each trace using
z-score normalization. The output traces are ready for direct coherence
computation without further preprocessing.
"""
import configparser
import json
import math
import os

from runtime.bandpass import apply_fir_bandpass


class TraceLoader:
    """Loads, filters, and whitens seismic receiver traces."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._source_dir = self._config.get("receivers", "source_dir")
        self._lowcut = self._config.getfloat("bandpass", "lowcut_hz")
        self._highcut = self._config.getfloat("bandpass", "highcut_hz")
        self._sample_rate = self._config.getfloat("bandpass", "sample_rate_hz")

    def load_traces(self):
        """Load all receiver traces from source directory.

        Each trace is bandpass-filtered to remove instrument noise outside
        the frequency band of interest, then whitened (z-score normalized)
        to unit variance for unbiased coherence estimation.

        Returns dict mapping receiver_id -> processed trace dict.
        """
        traces = {}
        data_dir = self._source_dir

        if not os.path.isdir(data_dir):
            return traces

        for fname in os.listdir(data_dir):
            if not fname.endswith(".json"):
                continue

            fpath = os.path.join(data_dir, fname)
            with open(fpath, "r") as f:
                data = json.load(f)

            recv_id = data["receiver_id"]
            raw_samples = data["samples"]

            # Apply bandpass filter to isolate seismic frequency band
            filtered = apply_fir_bandpass(
                raw_samples, self._sample_rate, self._lowcut, self._highcut
            )

            # Whiten the trace (z-score normalization)
            whitened = self._whiten(filtered)

            traces[recv_id] = {
                "receiver_id": recv_id,
                "sample_rate_hz": data["sample_rate_hz"],
                "num_samples": len(whitened),
                "samples": whitened,
            }

        return traces

    def _whiten(self, signal):
        """Apply z-score normalization to produce zero-mean unit-variance trace."""
        n = len(signal)
        if n == 0:
            return signal
        mean = sum(signal) / n
        variance = sum((v - mean) ** 2 for v in signal) / n
        std = math.sqrt(variance) if variance > 0 else 1.0
        return [(v - mean) / std for v in signal]
