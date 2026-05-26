"""
Ledger loader module — reads team allocation request files from the
configured source directory and returns them as a unified request list.
"""

import os
import json
import configparser


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
    return config


def load_team_ledgers(config):
    """
    Load all team ledger files from the source directory.
    Returns a list of (filename, requests) tuples in processing order.

    Files are sorted to ensure deterministic batch processing order.
    """
    source_dir = config.get("ledger", "source_dir")
    ledger_files = [f for f in os.listdir(source_dir) if f.endswith(".json")]

    ledger_files = sorted(ledger_files)

    results = []
    for filename in ledger_files:
        filepath = os.path.join(source_dir, filename)
        with open(filepath, "r") as fh:
            requests = json.load(fh)
        results.append((filename, requests))

    return results
