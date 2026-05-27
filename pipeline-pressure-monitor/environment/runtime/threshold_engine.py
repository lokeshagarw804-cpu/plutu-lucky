"""Threshold detection engine — identifies anomalous pressure events.

Detects sustained periods where pressure gradient magnitude exceeds the
configured threshold. Both positive gradients (surges) and negative
gradients (leaks/drops) are significant events that should be detected.
Events are classified by their dominant gradient direction.
"""
import configparser


# Bidirectional detection: both positive and negative gradient exceedances
DETECT_BIDIRECTIONAL = True


class ThresholdEngine:
    """Detects and classifies anomalous pressure gradient events."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat("detection", "pressure_threshold")
        self._min_duration = self._config.getint("detection", "min_duration_samples")
        self._classify = self._config.getboolean("detection", "classify_events")

    def detect_events(self, aggregated_windows):
        """Detect sustained threshold exceedances in windowed gradient data.

        An event is a consecutive run of windows where the gradient
        magnitude exceeds the threshold for at least min_duration_samples
        consecutive windows.

        Events are classified as:
        - "surge": sustained positive pressure increase
        - "leak": sustained negative pressure decrease
        """
        events = []

        for seg_id, agg_data in aggregated_windows.items():
            windows = agg_data["windows"]
            run_start = None
            run_length = 0

            for win in windows:
                mean_grad = win["mean_gradient"]

                # BUG: compares raw mean_gradient against threshold
                # instead of comparing mean_magnitude (absolute value)
                # This misses events where gradient is negative (leaks)
                if mean_grad > self._threshold:
                    if run_start is None:
                        run_start = win["window_index"]
                    run_length += 1
                else:
                    if run_length >= self._min_duration:
                        # BUG: always classifies as "surge" 
                        # Should check dominant direction in the run
                        events.append({
                            "segment_id": seg_id,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "type": "surge",
                            "peak_magnitude": self._get_peak_in_run(
                                windows, run_start, run_length
                            ),
                        })
                    run_start = None
                    run_length = 0

            # Check final run
            if run_length >= self._min_duration:
                events.append({
                    "segment_id": seg_id,
                    "start_window": run_start,
                    "end_window": run_start + run_length - 1,
                    "duration_windows": run_length,
                    "type": "surge",
                    "peak_magnitude": self._get_peak_in_run(
                        windows, run_start, run_length
                    ),
                })

        return events

    def _get_peak_in_run(self, windows, start, length):
        """Get peak gradient magnitude within an event run."""
        peak = 0.0
        for i in range(start, start + length):
            if i < len(windows):
                peak = max(peak, windows[i]["peak_value"])
        return round(peak, 6)
