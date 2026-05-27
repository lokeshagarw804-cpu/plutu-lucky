#!/usr/bin/env python3
"""Repair script for seismic waveform coherence pipeline.

Fixes five interacting defects:
A) coherence_engine.py re-applies bandpass filter on already-filtered traces
B) coherence_engine.py uses full Pearson on whitened data (double-normalization)
C) coherence_engine.py has off-by-one in window step calculation
D) phase_detector.py only detects positive coherence (missing abs)
E) grid_builder.py and run_correlator.py use string sort for receiver IDs
"""
import sys


def patch_coherence_engine():
    """Fix bugs A, B, C in the coherence engine."""
    path = "/app/runtime/coherence_engine.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: remove +1 from step calculation
    content = content.replace(
        "self._step = self._window_size - self._overlap + 1",
        "self._step = self._window_size - self._overlap"
    )

    # Fix Bug A: remove the redundant bandpass filter application
    # The traces are already filtered by trace_loader, so we use samples directly
    old_compute = '''    def compute_coherence(self, trace_a, trace_b):
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
        )'''

    new_compute = '''    def compute_coherence(self, trace_a, trace_b):
        """Compute per-window coherence between two prepared traces.

        Traces are expected to have been loaded and preprocessed by the
        trace loader (already filtered and whitened).

        Returns list of (window_index, coherence_coefficient) tuples.
        """
        samples_a = trace_a["samples"]
        samples_b = trace_b["samples"]'''

    content = content.replace(old_compute, new_compute)

    # Fix Bug B: replace Pearson with dot-product mean for whitened signals
    old_method = '''    def _compute_window_coherence(self, x, y):
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
        return max(-1.0, min(1.0, raw))'''

    new_method = '''    def _compute_window_coherence(self, x, y):
        """Compute coherence for whitened signal windows.

        Since traces are already globally whitened (zero mean, unit variance),
        the coherence reduces to the mean of element-wise products.
        """
        n = len(x)
        if n == 0:
            return 0.0

        raw = sum(x[i] * y[i] for i in range(n)) / n
        return max(-1.0, min(1.0, raw))'''

    content = content.replace(old_method, new_method)

    with open(path, "w") as f:
        f.write(content)


def patch_phase_detector():
    """Fix bug D: add absolute value for bidirectional detection."""
    path = "/app/runtime/phase_detector.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix threshold comparison to use abs()
    content = content.replace(
        "if coh > self._threshold:",
        "if abs(coh) > self._threshold:"
    )

    # Fix polarity classification (was always "constructive")
    old_append1 = '''                    if run_length >= self._min_duration:
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
                })'''

    new_append1 = '''                    if run_length >= self._min_duration:
                        polarity = "constructive" if windows[run_start][1] > 0 else "destructive"
                        phases.append({
                            "receiver_a": id_a,
                            "receiver_b": id_b,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "polarity": polarity,
                        })
                    run_start = None
                    run_length = 0

            # Handle final run at end of sequence
            if run_length >= self._min_duration:
                polarity = "constructive" if windows[run_start][1] > 0 else "destructive"
                phases.append({
                    "receiver_a": id_a,
                    "receiver_b": id_b,
                    "start_window": run_start,
                    "end_window": run_start + run_length - 1,
                    "duration_windows": run_length,
                    "polarity": polarity,
                })'''

    content = content.replace(old_append1, new_append1)

    with open(path, "w") as f:
        f.write(content)


def patch_grid_builder():
    """Fix bug E: sort by numeric suffix instead of string."""
    path = "/app/runtime/grid_builder.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "receiver_ids = sorted(traces.keys())",
        "receiver_ids = sorted(traces.keys(), key=lambda s: int(s.split('_')[1]))"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_run_correlator():
    """Fix bug E: sort by numeric suffix in main orchestration."""
    path = "/app/runtime/run_correlator.py"
    with open(path, "r") as f:
        content = f.read()

    content = content.replace(
        "receiver_ids = sorted(traces.keys())",
        "receiver_ids = sorted(traces.keys(), key=lambda s: int(s.split('_')[1]))"
    )

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_coherence_engine()
    patch_phase_detector()
    patch_grid_builder()
    patch_run_correlator()

    # Re-run the pipeline with fixes applied
    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_correlator import main as run_main
    run_main()


if __name__ == "__main__":
    main()
