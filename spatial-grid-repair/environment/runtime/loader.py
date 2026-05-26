"""Layer loader — reads geospatial point layers from data directory.

Loads JSON-format layer files containing spatial points. Only
layers whose type appears in the active_layers configuration
are loaded for spatial indexing.
"""
import configparser
import json
import os


class LayerLoader:
    """Loads spatial layers from data directory based on active config."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("sources", "data_dir")
        raw_layers = self._config.get("sources", "active_layers")
        self._active_layers = set(raw_layers.split(","))

    def load_layers(self):
        """Load all layer files and filter to active layer types.

        Returns dict mapping layer_id to layer data (with points list).
        Only layers whose layer_type appears in active_layers are loaded.
        """
        layers = {}
        for fname in sorted(os.listdir(self._data_dir)):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self._data_dir, fname)
            with open(fpath, "r") as f:
                data = json.load(f)

            layer_type = data.get("layer_type", "")
            if layer_type in self._active_layers:
                layers[data["layer_id"]] = data

        return layers
