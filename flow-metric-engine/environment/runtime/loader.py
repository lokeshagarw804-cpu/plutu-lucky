"""Packet capture loader — reads interface traffic data from JSON files."""
import configparser
import json
import os


class PacketLoader:
    """Loads raw packet capture data for configured interfaces."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_ifaces = self._config.get("interfaces", "active")
        self._active = [s.strip() for s in raw_ifaces.split(",")]
        self._source_dir = os.path.join(os.path.dirname(config_path), "data")

    def load_interfaces(self):
        """Load packet data for all active interfaces.

        Returns dict mapping interface_id to capture data.
        """
        interfaces = {}
        for iface_id in self._active:
            path = os.path.join(self._source_dir, f"{iface_id}.json")
            if not os.path.exists(path):
                continue
            with open(path, "r") as f:
                data = json.load(f)
            interfaces[iface_id] = {
                "interface_id": iface_id,
                "capture_start_ms": data["capture_start_ms"],
                "sample_interval_ms": data["sample_interval_ms"],
                "packets": data["packets"],
            }
        return interfaces
