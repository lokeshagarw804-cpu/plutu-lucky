"""
Per-cell statistical aggregation.

Computes summary statistics for each grid cell based on the
readings assigned to it.
"""

import configparser
from collections import defaultdict


class CellAggregator:
    """Computes per-cell statistics."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._min_readings = config.getint(
            "aggregation", "min_readings_per_cell"
        )
        self._variance_mode = config.get("aggregation", "variance_mode")

    def aggregate(self, assigned_readings):
        """Compute statistics per grid cell.

        Returns a dict mapping cell_id to aggregation results.
        Only cells with at least min_readings are included.
        """
        cells = defaultdict(list)
        for reading in assigned_readings:
            cells[reading["cell_id"]].append(reading)

        results = {}
        for cell_id, readings in cells.items():
            if len(readings) < self._min_readings:
                continue

            values = [r["value"] for r in readings]
            n = len(values)
            mean = sum(values) / n
            variance = sum((v - mean) ** 2 for v in values) / n
            std_dev = variance ** 0.5

            results[cell_id] = {
                "cell_id": cell_id,
                "cell_row": readings[0]["cell_row"],
                "cell_col": readings[0]["cell_col"],
                "count": n,
                "mean": round(mean, 4),
                "variance": round(variance, 4),
                "std_dev": round(std_dev, 4),
                "min_value": min(values),
                "max_value": max(values),
            }

        return results
