"""
Temporal alignment and windowing module.

Creates time-based processing windows from reading timestamps.
Windows are used by the correlator and event detector for
localized signal analysis.
"""

import configparser
from datetime import datetime, timedelta


class TemporalAligner:
    """Creates processing windows from timestamp ranges."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._window_size = config.getint("detection", "window_size")
        self._overlap_ratio = config.getfloat("detection", "overlap_ratio")

    def create_windows(self, readings):
        """Create overlapping time windows from reading timestamps.

        Windows are defined by the number of distinct timestamps they span.
        Adjacent windows overlap by the configured ratio.
        """
        timestamps = sorted(set(r["timestamp"] for r in readings))

        if len(timestamps) < self._window_size:
            return [(timestamps[0], timestamps[-1])]

        step = max(1, int(self._window_size * (1 - self._overlap_ratio)))
        windows = []

        for i in range(0, len(timestamps) - self._window_size + 1, step):
            start = timestamps[i]
            end = timestamps[i + self._window_size - 1]
            windows.append((start, end))

        return windows
