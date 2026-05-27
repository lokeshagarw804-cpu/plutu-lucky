"""Flow data loader — reads packet capture JSON files."""
import configparser
import json
import os


class FlowLoader:
    """Loads packet flow data for configured flows."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("flows", "data_dir")
        raw = self._config.get("flows", "active")
        self._active = [s.strip() for s in raw.split(",")]

    def load(self):
        """Load all active flows. Returns dict of flow_id -> data."""
        flows = {}
        for flow_id in self._active:
            path = os.path.join(self._data_dir, f"{flow_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            flows[flow_id] = data
        return flows
