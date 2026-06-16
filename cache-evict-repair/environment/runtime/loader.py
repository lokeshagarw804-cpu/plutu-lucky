"""Stream loader for client access requests.

Reads JSONL files from configured data directory and yields
request records per client stream.
"""
import json
import os
import configparser


def get_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
    return config


def load_client_stream(data_dir, client_name):
    """Load a single client's access stream from JSONL file.

    Args:
        data_dir: Path to directory containing client data files.
        client_name: Name of the client (used as filename prefix).

    Returns:
        List of request dicts with keys: key, seq, op.
    """
    filepath = os.path.join(data_dir, f"{client_name}.jsonl")
    requests = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                requests.append(json.loads(line))
    return requests


def load_all_streams(config):
    """Load all client streams from configured data directory.

    Returns:
        Dict mapping client_name -> list of request records.
    """
    data_dir = config.get("cache", "data_dir")
    streams = {}
    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith(".jsonl"):
            client_name = filename.replace(".jsonl", "")
            streams[client_name] = load_client_stream(data_dir, client_name)
    return streams
