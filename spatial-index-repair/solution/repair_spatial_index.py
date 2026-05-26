#!/usr/bin/env python3
"""Repair script for signal correlation engine."""
import os
import sys


def patch_correlator():
    """Fix window step calculation and remove double-normalization."""
    path = "/app/runtime/correlator.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug A: remove +1 from step calculation
    content = content.replace(
        "self._step = self._window_size - self._overlap + 1",
        "self._step = self._window_size - self._overlap"
    )

    # Fix Bug B: replace double-normalization with simple dot product
    # The _pearson_normalized method divides by local std again after global normalization
    # Replace it with a simple mean of element-wise products
    old_method = '''    def _pearson_normalized(self, x, y):
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

        return cov / (std_x * std_y)'''

    new_method = '''    def _pearson_normalized(self, x, y):
        """Correlation for pre-normalized signal windows.

        Since inputs are already z-score normalized globally, the window
        correlation is simply the mean of element-wise products.
        """
        n = len(x)
        if n == 0:
            return 0.0

        return sum(x[i] * y[i] for i in range(n)) / n'''

    content = content.replace(old_method, new_method)

    with open(path, "w") as f:
        f.write(content)


def patch_aligner():
    """Fix alignment offset calculation for fractional samples."""
    path = "/app/runtime/aligner.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug E: use round() instead of int() for offset calculation
    content = content.replace(
        "offset_a = int((align_start - start_a) * rate)",
        "offset_a = round((align_start - start_a) * rate)"
    )
    content = content.replace(
        "offset_b = int((align_start - start_b) * rate)",
        "offset_b = round((align_start - start_b) * rate)"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_matrix_builder():
    """Fix station ordering to use numeric sort."""
    path = "/app/runtime/matrix_builder.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: sort by numeric suffix instead of string
    content = content.replace(
        "station_ids = sorted(stations.keys())",
        "station_ids = sorted(stations.keys(), key=lambda s: int(s.split('_')[1]))"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_run_spatial():
    """Fix station ordering in main orchestration."""
    path = "/app/runtime/run_spatial.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug C: sort by numeric suffix in main loop too
    content = content.replace(
        "station_ids = sorted(stations.keys())",
        "station_ids = sorted(stations.keys(), key=lambda s: int(s.split('_')[1]))"
    )

    with open(path, "w") as f:
        f.write(content)


def patch_event_detector():
    """Fix threshold comparison to detect negative correlations."""
    path = "/app/runtime/event_detector.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix Bug D: use abs(corr) for threshold comparison
    content = content.replace(
        "if corr > self._threshold:",
        "if abs(corr) > self._threshold:"
    )

    # Fix event type classification
    old_type = '''                        events.append({
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
                })'''

    new_type = '''                        events.append({
                            "station_a": id_a,
                            "station_b": id_b,
                            "start_window": run_start,
                            "end_window": run_start + run_length - 1,
                            "duration_windows": run_length,
                            "type": "positive" if windows[run_start][1] > 0 else "negative",
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
                    "type": "positive" if windows[run_start][1] > 0 else "negative",
                })'''

    content = content.replace(old_type, new_type)

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_correlator()
    patch_aligner()
    patch_matrix_builder()
    patch_run_spatial()
    patch_event_detector()

    sys.path.insert(0, "/app")
    for key in list(sys.modules.keys()):
        if key.startswith("runtime"):
            del sys.modules[key]
    from runtime.run_spatial import main as run_main
    run_main()


if __name__ == "__main__":
    main()
