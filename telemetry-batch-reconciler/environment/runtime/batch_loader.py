"""
Batch loader - reads batch data and retry logs from disk.
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_batches():
    with open(os.path.join(DATA_DIR, "batches.json")) as f:
        return json.load(f)


def load_retry_log():
    with open(os.path.join(DATA_DIR, "retry_log.json")) as f:
        return json.load(f)


def load_settlements():
    with open(os.path.join(DATA_DIR, "settlements.json")) as f:
        return json.load(f)
