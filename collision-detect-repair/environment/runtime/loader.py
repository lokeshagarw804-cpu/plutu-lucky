"""Particle stream loader.

Reads JSONL simulation data from each stream directory and yields
particle records in submission order.
"""
import json
import os
from configparser import ConfigParser


class ParticleLoader:
    """Load particle position data from simulation streams."""

    def __init__(self, config: ConfigParser):
        self._data_dir = config.get("grid", "data_dir")

    def load_streams(self) -> list[dict]:
        """Load all particle streams and return sorted by stream then seq."""
        particles = []
        stream_files = sorted(f for f in os.listdir(self._data_dir)
                              if f.endswith(".jsonl"))
        for fname in stream_files:
            path = os.path.join(self._data_dir, fname)
            stream_name = fname.replace(".jsonl", "")
            with open(path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    record["stream"] = stream_name
                    particles.append(record)
        # Sort by stream name then sequence number
        particles.sort(key=lambda p: (p["stream"], p["seq"]))
        return particles
