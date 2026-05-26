"""Packet log ingestion — loads JSONL feeds from router nodes.

Reads packet records from each configured router node's log file,
validates required fields, and returns a unified list sorted by
timestamp for downstream processing.
"""
import configparser
import json
import os


class PacketIngestor:
    """Loads and merges packet logs from all router nodes."""

    REQUIRED_FIELDS = {"packet_id", "ts_ms", "seq", "src", "dst", "hops", "cost_per_hop", "ttl"}

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._data_dir = self._config.get("network", "data_dir")
        self._nodes = [n.strip() for n in self._config.get("network", "nodes").split(",")]

    def load_all(self):
        """Load packet records from all router node files.

        Returns list of validated packet records sorted by timestamp.
        """
        packets = []
        for node in self._nodes:
            filepath = os.path.join(self._data_dir, f"router_{node}.jsonl")
            if not os.path.isfile(filepath):
                continue
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    if self._validate(record):
                        packets.append(record)

        packets.sort(key=lambda p: (p["ts_ms"], p["packet_id"]))
        return packets

    def _validate(self, record):
        """Check that all required fields are present."""
        return self.REQUIRED_FIELDS.issubset(set(record.keys()))
