"""Spatial index builder — constructs bounding-box index over feature records.

Processes features in configurable batch sizes and maintains running
bounding-box envelopes for each spatial cell. The final index maps
each cell to its computed envelope after all batches are processed.
"""
import configparser
import math


class IndexBuilder:
    """Builds spatial cell index from geographic feature batches."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._batch_size = self._config.getint("index", "batch_size")
        self._algorithm = self._config.get("index", "algorithm")

    def build_index(self, all_features):
        """Build spatial index from feature list.

        Features are processed in batches. Each batch updates the
        bounding-box envelope for cells that contain features.

        Returns dict mapping cell_key to envelope dict with
        min_lat, max_lat, min_lon, max_lon, feature_count.
        """
        cells = {}
        n = len(all_features)

        for batch_start in range(0, n, self._batch_size):
            batch_end = min(batch_start + self._batch_size, n)
            batch = all_features[batch_start:batch_end]

            batch_cells = self._process_batch(batch)

            for cell_key, envelope in batch_cells.items():
                if cell_key not in cells:
                    cells[cell_key] = {
                        "min_lat": envelope["min_lat"],
                        "max_lat": envelope["max_lat"],
                        "min_lon": envelope["min_lon"],
                        "max_lon": envelope["max_lon"],
                        "feature_count": 0,
                    }
                # Expand envelope to include this batch
                cells[cell_key]["min_lat"] = min(
                    cells[cell_key]["min_lat"], envelope["min_lat"]
                )
                cells[cell_key]["max_lat"] = max(
                    cells[cell_key]["max_lat"], envelope["max_lat"]
                )
                cells[cell_key]["min_lon"] = min(
                    cells[cell_key]["min_lon"], envelope["min_lon"]
                )
                cells[cell_key]["max_lon"] = max(
                    cells[cell_key]["max_lon"], envelope["max_lon"]
                )
                # Note: feature_count tracks features in latest batch for cell
                cells[cell_key]["feature_count"] = envelope["feature_count"]

        return cells

    def _process_batch(self, batch):
        """Process a single batch of features into cell envelopes."""
        batch_cells = {}
        for feature in batch:
            lat = feature["lat"]
            lon = feature["lon"]
            cell_key = self._compute_cell_key(lat, lon)

            if cell_key not in batch_cells:
                batch_cells[cell_key] = {
                    "min_lat": lat,
                    "max_lat": lat,
                    "min_lon": lon,
                    "max_lon": lon,
                    "feature_count": 0,
                }

            env = batch_cells[cell_key]
            env["min_lat"] = min(env["min_lat"], lat)
            env["max_lat"] = max(env["max_lat"], lat)
            env["min_lon"] = min(env["min_lon"], lon)
            env["max_lon"] = max(env["max_lon"], lon)
            env["feature_count"] += 1

        return batch_cells

    def _compute_cell_key(self, lat, lon):
        """Compute grid cell key from coordinates (1-degree grid)."""
        cell_lat = int(math.floor(lat))
        cell_lon = int(math.floor(lon))
        return f"{cell_lat}_{cell_lon}"
