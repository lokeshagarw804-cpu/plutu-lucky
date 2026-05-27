"""
Aggregator - computes windowed statistics per batch after deduplication.

Produces per-batch summaries with:
  - event_count: number of events in the batch
  - mean_value: mean of event values (rounded to config precision)
  - min_value, max_value: extremes
  - sorted_events: events sorted by (ts, seq) for deterministic output

The sort MUST be stable per config (sort_stable = true).
"""
import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")


def load_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    return config


def aggregate_batch(batch):
    """Compute summary statistics for a single batch."""
    config = load_config()
    precision = int(config.get("pipeline", "precision"))
    sort_stable = config.getboolean("aggregation", "sort_stable")

    events = batch["events"]
    if not events:
        return {
            "batch_id": batch["batch_id"],
            "station": batch["station"],
            "event_count": 0,
            "mean_value": 0.0,
            "min_value": 0.0,
            "max_value": 0.0,
            "sorted_events": [],
        }

    # BUG: Uses sorted() without key specification for stable sort.
    # Python's sorted() is stable, but the key function here uses only 'ts'
    # without 'seq' as tiebreaker. For events with identical timestamps,
    # the order depends on input order which varies after dedup filtering.
    if sort_stable:
        sorted_events = sorted(events, key=lambda e: e["ts"])
    else:
        sorted_events = sorted(events, key=lambda e: (e["ts"], e["seq"]))

    values = [e["value"] for e in sorted_events]

    # BUG: Naive incremental mean calculation introduces floating-point drift
    # For small datasets it's negligible but causes precision issues at
    # exactly 4 decimal places when values have specific patterns.
    running_mean = 0.0
    for i, v in enumerate(values):
        running_mean = running_mean + (v - running_mean) / (i + 1)

    mean_val = round(running_mean, precision)
    min_val = round(min(values), precision)
    max_val = round(max(values), precision)

    return {
        "batch_id": batch["batch_id"],
        "station": batch["station"],
        "event_count": len(sorted_events),
        "mean_value": mean_val,
        "min_value": min_val,
        "max_value": max_val,
        "sorted_events": sorted_events,
    }


def aggregate_all(batches):
    """Aggregate all batches and return list of summaries."""
    return [aggregate_batch(b) for b in batches]
