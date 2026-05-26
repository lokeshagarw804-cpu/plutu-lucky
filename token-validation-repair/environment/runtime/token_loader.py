"""Token batch loader — reads token batch JSON files from the configured source directory."""

import json
import os
import configparser


def load_config():
    """Load configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read("/app/runtime/config.ini")
    return config


def load_batches(config=None):
    """Load all token batch files from the source directory.

    Returns a list of (filename, tokens) tuples in sorted file order.
    """
    if config is None:
        config = load_config()

    source_dir = config.get("tokens", "source_dir")
    batch_files = [f for f in os.listdir(source_dir) if f.endswith(".json")]

    # Sort files for deterministic ordering
    batch_files = sorted(batch_files)

    batches = []
    for filename in batch_files:
        filepath = os.path.join(source_dir, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
        batches.append((filename, data["tokens"]))

    return batches


def get_all_tokens(config=None):
    """Load and flatten all tokens from all batches in order."""
    batches = load_batches(config)
    all_tokens = []
    for filename, tokens in batches:
        all_tokens.extend(tokens)
    return all_tokens
