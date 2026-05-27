"""Phase detector — identifies sustained coherence phases.

Detects windows where coherence between receiver pairs exceeds the
configured threshold for a minimum number of consecutive windows.
Coherence phases indicate significant waveform coupling between
seismic receivers and are classified by their polarity.
"""
import configparser


class PhaseDetector:
    """Detects sustained coherence phases from windowed results."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._threshold = self._config.getfloat("phase_detection", "threshold")
        self._min_duration = self._config.getint("phase_detection", "min_duration_windows")

    def detect_phases(self, pair_coherences):
        """Detect sustained high-coherence phases across window sequences.

        A phase is a consecutive run of windows where coherence exceeds
        the configured threshold for at least min_duration_windows.
        Each phase is classified by its polarity (constructive/destructive).
        """
        phases = []

        for (id_a, id_b), windows in pair_coherences.items():
            run_start = None
            run_length = 0

            for win_idx, coh in windows:
                if coh > self._threshold:
                    if run_start is None:
                        run_start = win_idx
                    run_length += 1
                else:
                    if run_length >= self._min_duration:
                        phases.append({
                            "receiver_a": id_a,
                            "receiver_b": id_b,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "polarity": "constructive",
                        })
                    run_start = None
                    run_length = 0

            # Handle final run at end of sequence
            if run_length >= self._min_duration:
                phases.append({
                    "receiver_a": id_a,
                    "receiver_b": id_b,
                    "start_window": run_start,
                    "end_window": run_start + run_length - 1,
                    "duration_windows": run_length,
                    "polarity": "constructive",
                })

        return phases
