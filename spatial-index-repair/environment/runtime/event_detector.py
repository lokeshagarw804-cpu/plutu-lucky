"""Event detector — identifies significant correlation events.

Detects windows where correlation between station pairs exceeds the
configured threshold. Both positive and negative correlations can
indicate significant coupling between stations.
"""
import configparser


# Whether detection considers both positive and negative correlations
BIDIRECTIONAL_DETECTION = True


class EventDetector:
    """Detects significant correlation events from windowed results."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat("detection", "threshold")
        self._min_duration = self._config.getint("detection", "min_duration_windows")

    def detect_events(self, pair_correlations):
        """Detect sustained high-correlation events across window sequences.

        An event is a consecutive run of windows where correlation exceeds
        the threshold for at least min_duration_windows consecutive windows.
        """
        events = []

        for (id_a, id_b), windows in pair_correlations.items():
            run_start = None
            run_length = 0

            for win_idx, corr in windows:
                if corr > self._threshold:
                    if run_start is None:
                        run_start = win_idx
                    run_length += 1
                else:
                    if run_length >= self._min_duration:
                        events.append({
                            "station_a": id_a,
                            "station_b": id_b,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "type": "positive",
                        })
                    run_start = None
                    run_length = 0

            # Check final run
            if run_length >= self._min_duration:
                events.append({
                    "station_a": id_a,
                    "station_b": id_b,
                    "start_window": run_start,
                    "end_window": run_start + run_length - 1,
                    "duration_windows": run_length,
                    "type": "positive",
                })

        return events
