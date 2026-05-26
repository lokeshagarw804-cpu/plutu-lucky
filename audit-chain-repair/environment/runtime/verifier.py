"""Chain verifier — validates hash chain integrity per stream.

Processes hash chain results in verification windows and determines
which entries have broken chains (tampered). A window groups entries
into batches for reporting. The window size determines how many
entries are verified together.

Window count should be: ceil(entry_count / window_size).
"""
import configparser
import math


class ChainVerifier:
    """Verifies hash chain integrity across verification windows."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._window_size = self._config.getint("verification", "window_size")

    def verify_stream(self, chain_results, stream_id):
        """Verify chain integrity and report broken entries per window.

        Splits chain_results into windows and checks validity.
        Returns per-window verification summaries.
        """
        windows = []
        # Off-by-one: uses window_size + 1 as step
        for i in range(0, len(chain_results), self._window_size + 1):
            window_entries = chain_results[i:i + self._window_size + 1]
            broken = []
            valid_count = 0

            for entry_id, expected, stored, is_valid in window_entries:
                if is_valid:
                    valid_count += 1
                else:
                    broken.append(entry_id)

            windows.append({
                "window_id": len(windows),
                "stream_id": stream_id,
                "entry_count": len(window_entries),
                "valid_count": valid_count,
                "broken_count": len(broken),
                "broken_entries": broken,
            })

        return windows

    def get_window_count(self, entry_count):
        """Compute expected window count."""
        return math.ceil(entry_count / (self._window_size + 1))
